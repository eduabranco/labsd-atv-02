import socket
import threading
import json
import time
import hashlib
import mysql.connector
from config import NODES, DB_CONFIG

class DDBNode:
    def __init__(self, node_id):
        self.node_id = node_id
        self.host, self.port = NODES[node_id]
        self.peers = {k: v for k, v in NODES.items() if k != node_id}
        self.leader_id = max(NODES.keys()) # Assumimos o maior ID como líder inicial
        self.running = True
        self.active_nodes = set()
        
        # Conexão com Banco de Dados Local
        self.db = mysql.connector.connect(**DB_CONFIG)
        
        print(f"[*] Nó {self.node_id} iniciado em {self.host}:{self.port}")
        print(f"[*] Líder Atual: {self.leader_id}")

        # Threads
        threading.Thread(target=self.start_server, daemon=True).start()
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()
        
    # --- UTILITÁRIOS DE PROTOCOLO ---
    
    def calculate_checksum(self, data):
        """Gera MD5 do conteúdo para garantir integridade."""
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def send_message(self, target_ip, target_port, message):
        """Envia mensagem via Socket TCP com Checksum."""
        message['source_id'] = self.node_id
        message['checksum'] = self.calculate_checksum(message['payload'])
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect((target_ip, target_port))
                s.sendall(json.dumps(message).encode())
                # Espera ACK ou Resposta
                response = s.recv(4096).decode()
                return json.loads(response)
        except Exception as e:
            # print(f"[!] Falha ao conectar com {target_ip}:{target_port} - {e}")
            return None

    # --- SERVIDOR SOCKET (RECEBE REQUISIÇÕES) ---

    def start_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen(5)
        
        while self.running:
            client, addr = server.accept()
            threading.Thread(target=self.handle_client, args=(client,)).start()

    def handle_client(self, client_socket):
        try:
            data = client_socket.recv(4096).decode()
            if not data: return
            msg = json.loads(data)
            
            # Verificar Integridade
            if msg.get('checksum') and msg['checksum'] != self.calculate_checksum(msg['payload']):
                print("[!] Erro de Checksum: Dados corrompidos recebidos.")
                client_socket.send(json.dumps({'status': 'error', 'msg': 'Checksum fail'}).encode())
                return

            msg_type = msg['type']
            payload = msg['payload']
            response = {'status': 'ok'}

            # LOGICA DE MENSAGENS
            if msg_type == 'HEARTBEAT':
                self.active_nodes.add(msg['source_id'])
                # Se receber HB de um ID maior, ele é o lider
                if msg['source_id'] > self.leader_id:
                    self.leader_id = msg['source_id']
            
            elif msg_type == 'ELECTION':
                # Algoritmo Bully: Se receber de ID menor, eu respondo OK e inicio eleição
                print(f"[*] Recebido Eleição de {msg['source_id']}")
                response['status'] = 'ALIVE'

            elif msg_type == 'VICTORY':
                self.leader_id = msg['source_id']
                print(f"[*] Novo Líder Eleito: {self.leader_id}")

            elif msg_type == 'EXECUTE_QUERY':
                print(f"[*] Query Recebida: {payload['query']}")
                response = self.process_query(payload['query'])

            elif msg_type == 'REPLICATE':
                # Recebe ordem do líder para commitar alteração (2PC Fase 2 implícita)
                print(f"[*] Replicando dados do Líder...")
                self.execute_local_query(payload['query'])

            client_socket.send(json.dumps(response).encode())

        except Exception as e:
            print(f"[!] Erro no handler: {e}")
        finally:
            client_socket.close()

    # --- LÓGICA DE BANCO DE DADOS E REPLICAÇÃO ---

    def execute_local_query(self, query):
        """Executa no MySQL Local."""
        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute(query)
            if query.strip().upper().startswith("SELECT"):
                res = cursor.fetchall()
                return {'status': 'success', 'data': res, 'node': self.node_id}
            else:
                self.db.commit()
                return {'status': 'success', 'data': 'Commited', 'node': self.node_id}
        except mysql.connector.Error as err:
            return {'status': 'error', 'msg': str(err)}

    def process_query(self, query):
        """Lógica de Distribuição (Load Balancer / Replication)."""
        is_write = not query.strip().upper().startswith("SELECT")
        
        # 1. Se for LEITURA (SELECT), executa localmente (Balanceamento distribuído)
        if not is_write:
            return self.execute_local_query(query)

        # 2. Se for ESCRITA (INSERT/UPDATE/DELETE)
        # Se eu não sou o líder, encaminho para o líder
        if self.node_id != self.leader_id:
            print(f"[*] Encaminhando escrita para o Líder {self.leader_id}")
            leader_ip, leader_port = NODES[self.leader_id]
            msg = {'type': 'EXECUTE_QUERY', 'payload': {'query': query}}
            return self.send_message(leader_ip, leader_port, msg)
        
        # Se eu SOU o líder, coordeno a replicação (ACID Simplificado)
        else:
            print("[*] Sou o Líder. Iniciando Replicação...")
            # Passo 1: Executa local
            local_res = self.execute_local_query(query)
            if local_res['status'] == 'error':
                return local_res
            
            # Passo 2: Broadcast para todos os outros nós (Replicação)
            success_count = 1
            for nid, (nip, nport) in self.peers.items():
                if nid in self.active_nodes:
                    msg = {'type': 'REPLICATE', 'payload': {'query': query}}
                    res = self.send_message(nip, nport, msg)
                    if res and res.get('status') == 'success':
                        success_count += 1
            
            return {'status': 'success', 'msg': f'Query replicada em {success_count} nós', 'node': self.node_id}

    # --- HEARTBEAT E ELEIÇÃO ---

    def start_election(self):
        print("[!] Líder inativo detectado. Iniciando Eleição (Bully)...")
        higher_nodes = [nid for nid in NODES if nid > self.node_id]
        
        if not higher_nodes:
            # Sou o maior ID, sou o líder!
            self.become_leader()
            return

        answers = 0
        for nid in higher_nodes:
            ip, port = NODES[nid]
            res = self.send_message(ip, port, {'type': 'ELECTION', 'payload': {}})
            if res and res.get('status') == 'ALIVE':
                answers += 1
        
        if answers == 0:
            self.become_leader()

    def become_leader(self):
        self.leader_id = self.node_id
        print(f"[*] EU SOU O NOVO LÍDER (Nó {self.node_id})")
        # Avisar a todos
        msg = {'type': 'VICTORY', 'payload': {}}
        for nid, (ip, port) in self.peers.items():
            self.send_message(ip, port, msg)

    def heartbeat_loop(self):
        """Informa que está ativo e verifica o líder."""
        while self.running:
            # Enviar Heartbeat para todos (Gossip / Broadcast)
            msg = {'type': 'HEARTBEAT', 'payload': {'timestamp': time.time()}}
            
            # Resetar lista de ativos para verificar quem responde no próximo ciclo
            # (Numa impl real, usaria timeout mais sofisticado)
            current_active = list(self.active_nodes)
            self.active_nodes.clear() 
            self.active_nodes.add(self.node_id) # Eu estou ativo

            for nid, (ip, port) in self.peers.items():
                res = self.send_message(ip, port, msg)
                if res:
                    self.active_nodes.add(nid)
            
            # Verificar se Líder caiu
            if self.leader_id not in self.active_nodes and self.leader_id != self.node_id:
                # O Líder não respondeu neste ciclo
                self.start_election()

            time.sleep(5) # Periodo de 5 segundos

# --- ENTRY POINT ---
if __name__ == "__main__":
    import sys
    # Para rodar: python middleware.py <NODE_ID>
    if len(sys.argv) != 2:
        print("Uso: python middleware.py <NODE_ID>")
        sys.exit(1)
    
    my_id = int(sys.argv[1])
    node = DDBNode(my_id)
    
    # Mantém a main thread viva
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("Desligando...")