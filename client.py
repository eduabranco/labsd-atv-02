from socket import socket, AF_INET, SOCK_STREAM
from json import loads, dumps
from random import choice
from hashlib import md5
from config import NODES
from typing import Any

def calculate_checksum(data: dict[str, Any]) -> str:
    return md5(dumps(data, sort_keys = True).encode()).hexdigest()

def send_query(query: str) -> dict[str, Any]:
    # Escolhe um nó aleatório para Load Balancing inicial
    node_id = choice(list(NODES.keys()))
    ip, port = NODES[node_id]

    msg = {
        'type': 'EXECUTE_QUERY',
        'payload': {'query': query}
    }

    msg['checksum'] = calculate_checksum(msg['payload'])
    msg['source_id'] = 0 # 0 representa cliente externo

    print(f"--- Conectando ao Nó {node_id} ({ip}: {port}) ---")

    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.settimeout(5)
        s.connect((ip, port))
        s.sendall(dumps(msg).encode())

        resp = s.recv(4096).decode()
        if not resp:
            s.close()
            return {'status': 'error', 'msg': 'No response from server'}

        data = loads(resp)
        s.close()
        return data
    except Exception as e:
        return {'status': 'error', 'msg': str(e)}

def main():
    print("=== DDB Client Interface ===")
    print("Digite suas queries SQL (ou 'sair').")
    print("Para queries multi-linha, termine com ';' em uma linha sozinho.")

    while True:
        lines = []
        print("\nSQL> ", end='')
        while True:
            line = input()
            if line.lower() == 'sair':
                return
            if line.strip() == ';':
                break
            lines.append(line)
            if not lines[0]:  # Se primeira linha vazia, sai do loop
                break
            print("...> ", end='')
        
        query = '\n'.join(lines).strip()
        if not query:
            continue

        result = send_query(query)

        if not result:
            print("[Erro] No response received from server")
            continue

        if result.get('status') == 'success':
            print(f"\n[✓ Sucesso] Executado no Nó: {result.get('node')}")
            
            # Exibir dados se existirem
            if 'data' in result and result['data']:
                data = result['data']
                if isinstance(data, list) and len(data) > 0:
                    print(f"\n📊 Resultados ({len(data)} linhas):")
                    for idx, row in enumerate(data, 1):
                        print(f"  [{idx}] {row}")
                elif isinstance(data, str):
                    print(f"Resultado: {data}")
                else:
                    print(f"Dados: {data}")
            
            # Exibir informações adicionais (2PC)
            if 'msg' in result:
                print(f"💬 Info: {result['msg']}")
            
            if 'nodes' in result:
                print(f"📍 Nós envolvidos: {result['nodes']}")
        else:
            print(f"\n[✗ Erro] {result.get('msg', 'Erro desconhecido')}")

if __name__ == "__main__": main()