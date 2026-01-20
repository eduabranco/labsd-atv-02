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

    while True:
        query = input("\nSQL> ")
        if query.lower() == 'sair': break

        result = send_query(query)

        if not result:
            print("[Erro] No response received from server")
            continue

        if result.get('status') == 'success':
            print(f"[Sucesso] Executado no Nó: {result.get('node')}")
            if 'data' in result:
                print("Dados:", result['data'])
            if 'msg' in result:
                print("Msg:", result['msg'])
        else:
            print(f"[Erro] {result.get('msg')}")

if __name__ == "__main__": main()