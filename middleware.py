from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread, Lock
from json import loads, dumps
from time import sleep, time
from hashlib import md5
from mysql.connector import Error, connect
from config import NODES, DB_CONFIG
from typing import Any
from sys import argv

class DDBNode:
    def __init__(self, node_id: int) -> None:
        self.node_id = node_id
        self.host, self.port = NODES[node_id]
        self.peers = {k: v for k, v in NODES.items() if k != node_id}
        self.leader_id = max(NODES.keys()) # Assumimos o maior ID como líder inicial
        self.running = True
        self.active_nodes = set()

        # Conexão com Banco de Dados Local
        self.db = connect(**DB_CONFIG)
        self.db.autocommit = False  # Desabilita autocommit para transações 2PC

        # Controle de transações 2PC
        self.pending_transaction = None  # Armazena query em preparação
        self.transaction_lock = Lock()

        print(f"[*] Nó {self.node_id} iniciado em {self.host}:{self.port}")
        print(f"[*] Líder Atual: {self.leader_id}")
        print(f"[*] 2PC (Two-Phase Commit) Ativado")

        # Threads
        Thread(target = self.start_server, daemon = True).start()
        Thread(target = self.heartbeat_loop, daemon = True).start()

    # --- UTILITÁRIOS DE PROTOCOLO ---

    def calculate_checksum(self, data: Any) -> str:
        """Gera MD5 do conteúdo para garantir integridade."""
        return md5(dumps(data, sort_keys = True).encode()).hexdigest()

    def send_message(self,
        target_ip: str,
        target_port: int,
        message: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Envia mensagem via Socket TCP com checksum de integridade."""
        message["source_id"] = self.node_id
        message["checksum"] = self.calculate_checksum(message["payload"])

        try:
            with socket(AF_INET, SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect((target_ip, target_port))
                s.sendall(dumps(message).encode())
                # Espera ACK ou Resposta
                return loads(s.recv(4096).decode())
        except Exception as e:
            print(f"[!] Falha ao conectar com {target_ip}: {target_port} - {e}")
            return None

    def start_server(self):
        server = socket(AF_INET, SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen(5)

        while self.running:
            client, addr = server.accept()
            Thread(target = self.handle_client, args = [client]).start()

    def handle_client(self, client_socket: socket) -> None:
        try:
            data = client_socket.recv(4096).decode()
            if not data: return
            msg: dict[str, Any] = loads(data)

            # Verificar Integridade
            if msg.get("checksum") and msg["checksum"] != self.calculate_checksum(msg["payload"]):
                print("[!] Erro de Checksum: Dados corrompidos recebidos.")
                client_socket.send(dumps({"status": "error", "msg": "Checksum fail"}).encode())
                return

            msg_type = msg["type"]
            payload = msg["payload"]
            response = {"status": "ok"}

            # LOGICA DE MENSAGENS
            match msg_type:
                case "HEARTBEAT":
                    self.active_nodes.add(msg["source_id"])
                    # Se receber HB de um ID maior, ele é o lider
                    if msg["source_id"] > self.leader_id:
                        self.leader_id = msg["source_id"]

                case "ELECTION":
                    # Algoritmo Bully: Se receber de ID menor, eu respondo OK e inicio eleição
                    print(f"[*] Recebido Eleição de {msg["source_id"]}")
                    response["status"] = "ALIVE"

                case "VICTORY":
                    self.leader_id = msg["source_id"]
                    print(f"[*] Novo Líder Eleito: {self.leader_id}")

                case "EXECUTE_QUERY":
                    print(f"[*] Query Recebida: {payload["query"]}")
                    response = self.process_query(payload["query"])

                case "PREPARE":
                    # 2PC Fase 1: PREPARE - Valida se pode executar a query
                    print(f"[*] [2PC-PREPARE] Validando query: {payload["query"]}")
                    response = self.handle_prepare(payload["query"])

                case "COMMIT":
                    # 2PC Fase 2: COMMIT - Confirma a transação
                    print(f"[*] [2PC-COMMIT] Commitando transação")
                    response = self.handle_commit()

                case "ABORT":
                    # 2PC Fase 2: ABORT - Reverte a transação
                    print(f"[*] [2PC-ABORT] Abortando transação")
                    response = self.handle_abort()
                
                case _:
                    response = {"status": "error", "msg": "Tipo de mensagem desconhecido"}

            client_socket.send(dumps(response).encode())

        except Exception as e:
            print(f"[!] Erro no handler: {e}")

        finally:
            client_socket.close()

    # --- LÓGICA DE BANCO DE DADOS E REPLICAÇÃO ---

    def execute_local_query(self,
        query: str,
        commit: bool = True
    ) -> dict[str, Any]:
        """Executa no MySQL Local."""
        try:
            cursor = self.db.cursor(dictionary = True)
            cursor.execute(query)
            if query.strip().upper().startswith("SELECT"):
                res = cursor.fetchall()
                return {"status": "success", "data": res, "node": self.node_id}
            else:
                if commit: self.db.commit()
                return {"status": "success", "data": "Commited", "node": self.node_id}
        except Error as err:
            return {"status": "error", "msg": str(err)}

    # --- 2PC (TWO-PHASE COMMIT) HANDLERS ---

    def handle_prepare(self, query: str) -> dict[str, Any]:
        """
        2PC Fase 1 - PREPARE: Valida a query e prepara para commit.
        Retorna VOTE_YES se pode executar, VOTE_NO caso contrário.
        """
        with self.transaction_lock:
            try:
                # Tenta executar a query sem commit
                cursor = self.db.cursor(dictionary = True)
                cursor.execute(query)

                # Armazena a query pendente
                self.pending_transaction = query

                print(f"[*] [2PC-PREPARE] VOTE_YES - Query válida")
                return {"status": "VOTE_YES", "node": self.node_id}

            except Error as err:
                # Se houver erro, faz rollback e vota NÃO
                self.db.rollback()
                self.pending_transaction = None
                print(f"[!] [2PC-PREPARE] VOTE_NO - Erro: {err}")
                return {"status": "VOTE_NO", "msg": str(err), "node": self.node_id}

    def handle_commit(self) -> dict[str, Any]:
        """
        2PC Fase 2 - COMMIT: Confirma a transação preparada.
        """
        with self.transaction_lock:
            try:
                if self.pending_transaction:
                    self.db.commit()
                    print(f"[*] [2PC-COMMIT] Transação confirmada com sucesso")
                    self.pending_transaction = None
                    return {"status": "success", "node": self.node_id}
                else:
                    return {"status": "error", "msg": "Nenhuma transação pendente"}
            except Error as err:
                self.db.rollback()
                self.pending_transaction = None
                return {"status": "error", "msg": str(err)}

    def handle_abort(self) -> dict[str, Any]:
        """
        2PC Fase 2 - ABORT: Reverte a transação preparada.
        """
        with self.transaction_lock:
            try:
                self.db.rollback()
                print(f"[*] [2PC-ABORT] Transação revertida")
                self.pending_transaction = None
                return {"status": "success", "node": self.node_id}
            except Error as err:
                return {"status": "error", "msg": str(err)}

    def process_query(self, query) -> dict[str, Any] | None:
        """Distribui queries: leituras locais, escritas via 2PC coordenado pelo líder."""
        is_write = not query.strip().upper().startswith("SELECT")

        # 1. Se for LEITURA (SELECT), executa localmente (Balanceamento distribuído)
        if not is_write:
            return self.execute_local_query(query)

        # 2. Se for ESCRITA (INSERT/UPDATE/DELETE)
        # Se eu não sou o líder, encaminho para o líder
        if self.node_id != self.leader_id:
            print(f"[*] Encaminhando escrita para o Líder {self.leader_id}")
            leader_ip, leader_port = NODES[self.leader_id]
            msg = {"type": "EXECUTE_QUERY", "payload": {"query": query}}
            return self.send_message(leader_ip, leader_port, msg)

        # Se eu SOU o líder, coordeno o 2PC

        return self.execute_2pc(query)

    def execute_2pc(self, query) -> dict[str, Any]:
        """
        Executa Two-Phase Commit completo:
        FASE 1 (PREPARE): Pergunta a todos se podem executar
        FASE 2 (COMMIT/ABORT): Decide baseado nos votos
        """
        print(f"[*] [2PC] Iniciando Two-Phase Commit como Coordenador")

        # === FASE 1: PREPARE ===
        print(f"[*] [2PC-FASE-1] Enviando PREPARE para todos os nós")

        # Primeiro, prepara localmente
        local_prepare = self.handle_prepare(query)
        if local_prepare["status"] != "VOTE_YES":
            print(f"[!] [2PC] Falha na preparação local. Abortando.")
            return {"status": "error", "msg": "Falha na preparação local", "node": self.node_id}

        # Coleta votos dos participantes
        votes = {"YES": 1, "NO": 0}  # Líder já votou YES
        failed_nodes = []

        for nid, (nip, nport) in self.peers.items():
            if nid in self.active_nodes:
                msg = {"type": "PREPARE", "payload": {"query": query}}
                res = self.send_message(nip, nport, msg)

                if res and res.get("status") == "VOTE_YES":
                    votes["YES"] += 1
                    print(f"[*] [2PC-FASE-1] Nó {nid}: VOTE_YES")
                else:
                    votes["NO"] += 1
                    failed_nodes.append(nid)
                    print(f"[!] [2PC-FASE-1] Nó {nid}: VOTE_NO")
            else:
                print(f"[!] [2PC-FASE-1] Nó {nid} inativo - não participará")

        # === DECISÃO ===
        decision = "COMMIT" if votes["NO"] == 0 else "ABORT"

        print(f"[*] [2PC-DECISÃO] Votos: {votes["YES"] = }, {votes["NO"] = } -> {decision}")

        # === FASE 2: COMMIT ou ABORT ===
        print(f"[*] [2PC-FASE-2] Enviando {decision} para todos os nós")

        # Executa decisão localmente
        if decision == "COMMIT":
            local_result = self.handle_commit()
        else:
            local_result = self.handle_abort()
            return {"status": "error", "msg": f"Transação abortada. Nós com falha: {failed_nodes}", "node": self.node_id}

        # Envia decisão para todos os participantes
        committed_nodes = [self.node_id]
        for nid, (nip, nport) in self.peers.items():
            if nid in self.active_nodes:
                msg = {"type": decision, "payload": {}}
                res = self.send_message(nip, nport, msg)
                if res and res.get("status") == "success":
                    committed_nodes.append(nid)
                    print(f"[*] [2PC-FASE-2] Nó {nid}: {decision} confirmado")

        print(f"[*] [2PC-COMPLETO] Transação commitada em {len(committed_nodes)} nós: {committed_nodes}")
        return {
            "status": "success", 
            "msg": f"2PC completo. Commitado em {len(committed_nodes)} nós", 
            "nodes": committed_nodes,
            "node": self.node_id
        }

    # --- HEARTBEAT E ELEIÇÃO ---

    def start_election(self) -> None:
        print("[!] Líder inativo detectado. Iniciando Eleição (Bully)...")
        higher_nodes = [nid for nid in NODES if nid > self.node_id]

        if not higher_nodes:
            # Sou o maior ID, sou o líder!
            self.become_leader()
            return

        answers = 0
        for nid in higher_nodes:
            ip, port = NODES[nid]
            res = self.send_message(ip, port, {"type": "ELECTION", "payload": {}})
            if res and res.get("status") == "ALIVE":
                answers += 1

        if answers == 0:
            self.become_leader()

    def become_leader(self) -> None:
        self.leader_id = self.node_id
        print(f"[*] EU SOU O NOVO LÍDER (Nó {self.node_id})")
        # Avisar a todos
        msg = {"type": "VICTORY", "payload": {}}
        for nid, (ip, port) in self.peers.items():
            self.send_message(ip, port, msg)

    def heartbeat_loop(self) -> None:
        """Envia heartbeats periódicos e detecta falha do líder."""
        while self.running:
            # Enviar Heartbeat para todos (Gossip / Broadcast)
            msg = {"type": "HEARTBEAT", "payload": {"timestamp": time()}}

            # Resetar lista de ativos para verificar quem responde no próximo ciclo
            self.active_nodes.clear() 
            self.active_nodes.add(self.node_id) # Eu estou ativo

            for nid, (ip, port) in self.peers.items():
                res = self.send_message(ip, port, msg)
                if res: self.active_nodes.add(nid)

            # Verificar se Líder caiu
            if self.leader_id not in self.active_nodes and self.leader_id != self.node_id:
                # O Líder não respondeu neste ciclo
                self.start_election()

            sleep(5)

# --- ENTRY POINT ---
if __name__ == "__main__":
    # Para rodar: python middleware.py <NODE_ID>
    if len(argv) != 2:
        print("Uso: python middleware.py <NODE_ID>")
        exit(1)

    my_id = int(argv[1])
    node = DDBNode(my_id)

    # Mantém a main thread viva
    try:
        while True: sleep(1)
    except KeyboardInterrupt:
        print("Desligando...")