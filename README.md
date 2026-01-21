# SGBD Distribuído com MySQL

Sistema de banco de dados distribuído com replicação automática, eleição de líder e garantias **ACID completas** via protocolo Two-Phase Commit (2PC).

## Quick Start

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar MySQL
```bash
python3 db_setup.py  # Auto-detecta configuração e cria banco/tabelas
```

### 3. Configurar Nós
Edite [config.py](config.py):
```python
NODES = {
    1: ('192.168.1.10', 5001),
    2: ('192.168.1.11', 5002),
    3: ('192.168.1.12', 5003)
}

# Leituras consistentes (opcional)
CONSISTENT_READS = False  # True = leituras via líder (slower, mais consistente)
                          # False = leituras locais (faster, eventual consistency)
```

### 4. Iniciar Sistema
```bash
python middleware.py 1  # Terminal 1
python middleware.py 2  # Terminal 2
python middleware.py 3  # Terminal 3
python client.py        # Cliente
```

## Arquitetura

* **Topologia:** Peer-to-Peer com líder dinâmico
* **Comunicação:** TCP Sockets com mensagens JSON + MD5 checksum
* **Consistência:** Two-Phase Commit (2PC) para garantias ACID
  - Fase 1 (PREPARE): Validação em todos os nós
  - Fase 2 (COMMIT/ABORT): Decisão atômica baseada em votação
  - **Recovery Log**: Logging de decisões do coordenador para durabilidade
  - **Timeout**: 30s para transações preparadas (previne deadlocks)
* **Isolamento:** REPEATABLE READ (previne dirty reads e non-repeatable reads)
* **Eleição:** Algoritmo Bully (maior ID assume como líder)
* **Heartbeat:** 5 segundos (detecção rápida de falhas)
* **Banco:** MySQL local em cada nó

## Uso do Cliente

```sql
SQL> INSERT INTO usuarios (nome, email) VALUES ('João', 'joao@teste.com');
SQL> SELECT * FROM usuarios;
SQL> UPDATE usuarios SET email = 'novo@email.com' WHERE id = 1;
SQL> DELETE FROM usuarios WHERE id = 1;
```

## Teste de Falha

1. Mate o processo do líder (maior ID)
2. Aguarde 5-10 segundos
3. Observe eleição automática de novo líder nos logs
4. Sistema continua operacional

## Teste de Recovery

1. Inicie uma transação e mate o coordenador durante a fase PREPARE
2. Reinicie o nó
3. Recovery automático irá abortar transações pendentes e limpar o log
4. Verifique os arquivos `recovery_log_node_X.json` para ver o histórico

## Solução de Problemas

**Erro MySQL Access Denied:**
```bash
python3 db_setup.py  # Re-executa auto-detecção
```

**Nós não se comunicam:**
- Verifique IPs em [config.py](config.py)
- Teste: `ping <IP_DO_NÓ>`
- Libere portas: `sudo ufw allow 5001:5003/tcp`

## Arquivos Principais

- [middleware.py](middleware.py) - Servidor do nó distribuído
- [client.py](client.py) - Cliente SQL
- [config.py](config.py) - Configuração de rede
- [db_setup.py](db_setup.py) - Setup automático MySQL


