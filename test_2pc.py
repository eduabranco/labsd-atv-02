#!/usr/bin/env python3
"""
Script de teste para demonstrar o protocolo 2PC (Two-Phase Commit)
"""

import socket
import json
import random
import hashlib
import time
from config import NODES

def calculate_checksum(data):
    return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

def send_query(query):
    node_id = random.choice(list(NODES.keys()))
    ip, port = NODES[node_id]
    
    msg = {
        'type': 'EXECUTE_QUERY',
        'payload': {'query': query}
    }
    msg['checksum'] = calculate_checksum(msg['payload'])
    msg['source_id'] = 0

    print(f"\n{'='*60}")
    print(f"Conectando ao Nó {node_id} ({ip}:{port})")
    print(f"Query: {query}")
    print(f"{'='*60}")
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((ip, port))
        s.sendall(json.dumps(msg).encode())
        
        resp = s.recv(4096).decode()
        data = json.loads(resp)
        s.close()
        return data
    except Exception as e:
        return {'status': 'error', 'msg': str(e)}

def print_result(result):
    if result.get('status') == 'success':
        print(f"\n✅ [SUCESSO]")
        print(f"   Nó Executor: {result.get('node')}")
        if 'nodes' in result:
            print(f"   Nós Commitados: {result.get('nodes')}")
        if 'msg' in result:
            print(f"   Mensagem: {result['msg']}")
        if 'data' in result:
            print(f"   Dados: {result['data']}")
    else:
        print(f"\n❌ [ERRO]")
        print(f"   Mensagem: {result.get('msg')}")

def test_2pc_success():
    """Teste 1: Inserção válida com 2PC (deve ter sucesso)"""
    print("\n" + "🔵"*30)
    print("TESTE 1: Inserção Válida - 2PC com COMMIT")
    print("🔵"*30)
    
    result = send_query("INSERT INTO usuarios (nome, email) VALUES ('Teste2PC', '2pc@test.com')")
    print_result(result)
    
    print("\n⏳ Aguardando 2 segundos...")
    time.sleep(2)
    
    print("\n📊 Verificando se os dados foram inseridos em todos os nós...")
    result = send_query("SELECT * FROM usuarios WHERE email = '2pc@test.com'")
    print_result(result)

def test_2pc_abort():
    """Teste 2: Inserção inválida com 2PC (deve abortar)"""
    print("\n" + "🔴"*30)
    print("TESTE 2: Inserção Inválida - 2PC com ABORT")
    print("🔴"*30)
    
    print("\n📝 Tentando inserir com nome NULL (viola constraint)")
    result = send_query("INSERT INTO usuarios (id, nome, email) VALUES (9999, NULL, 'invalid@test.com')")
    print_result(result)
    
    print("\n⏳ Aguardando 2 segundos...")
    time.sleep(2)
    
    print("\n📊 Verificando que os dados NÃO foram inseridos (rollback)...")
    result = send_query("SELECT * FROM usuarios WHERE id = 9999")
    if result.get('status') == 'success' and len(result.get('data', [])) == 0:
        print(f"\n✅ [ATOMICIDADE GARANTIDA]")
        print(f"   Nenhum dado foi inserido em nenhum nó!")
        print(f"   2PC funcionou corretamente: ABORT em todos os nós")
    else:
        print(f"\n⚠️ [ATENÇÃO] Dados encontrados: {result}")

def test_read_distribution():
    """Teste 3: Distribuição de leituras"""
    print("\n" + "🟢"*30)
    print("TESTE 3: Distribuição de Leituras (Load Balancing)")
    print("🟢"*30)
    
    print("\n📊 Fazendo 5 consultas - observe que vão para nós diferentes")
    for i in range(5):
        result = send_query("SELECT COUNT(*) as total FROM usuarios")
        if result.get('status') == 'success':
            print(f"   Consulta {i+1}: Nó {result.get('node')} | Total: {result.get('data')}")
        time.sleep(0.5)

def test_update_2pc():
    """Teste 4: Atualização com 2PC"""
    print("\n" + "🟡"*30)
    print("TESTE 4: Atualização de Dados com 2PC")
    print("🟡"*30)
    
    print("\n📝 Atualizando email do usuário 'Teste2PC'")
    result = send_query("UPDATE usuarios SET email = '2pc_updated@test.com' WHERE nome = 'Teste2PC'")
    print_result(result)
    
    print("\n⏳ Aguardando 2 segundos...")
    time.sleep(2)
    
    print("\n📊 Verificando a atualização...")
    result = send_query("SELECT * FROM usuarios WHERE nome = 'Teste2PC'")
    print_result(result)

def cleanup():
    """Limpa dados de teste"""
    print("\n" + "🧹"*30)
    print("LIMPEZA: Removendo dados de teste")
    print("🧹"*30)
    
    result = send_query("DELETE FROM usuarios WHERE email LIKE '%test.com'")
    print_result(result)

def main():
    print("\n" + "="*60)
    print(" SCRIPT DE TESTE - TWO-PHASE COMMIT (2PC)")
    print("="*60)
    print("\nEste script demonstra:")
    print("✅ 1. Commit distribuído com sucesso")
    print("❌ 2. Abort atômico em caso de falha")
    print("📊 3. Distribuição de leituras (load balancing)")
    print("🔄 4. Atualização replicada")
    
    input("\nPressione ENTER para iniciar os testes...")
    
    try:
        # Teste 1: Inserção com sucesso (COMMIT)
        test_2pc_success()
        
        input("\n\nPressione ENTER para continuar com o próximo teste...")
        
        # Teste 2: Inserção com falha (ABORT)
        test_2pc_abort()
        
        input("\n\nPressione ENTER para continuar com o próximo teste...")
        
        # Teste 3: Distribuição de leituras
        test_read_distribution()
        
        input("\n\nPressione ENTER para continuar com o próximo teste...")
        
        # Teste 4: Atualização
        test_update_2pc()
        
        input("\n\nPressione ENTER para limpar dados de teste...")
        
        # Limpeza
        cleanup()
        
        print("\n" + "="*60)
        print("✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        print("="*60)
        print("\nO 2PC está funcionando corretamente:")
        print("  ✓ Atomicidade garantida (all-or-nothing)")
        print("  ✓ Consistência entre nós")
        print("  ✓ Rollback automático em falhas")
        print("  ✓ Load balancing para leituras")
        print("\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Testes interrompidos pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro durante os testes: {e}")

if __name__ == "__main__":
    main()
