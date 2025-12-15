# Banco de Dados Distribuído - Middleware MySQL

Sistema de banco de dados distribuído (DDB) desenvolvido em Java usando MySQL como SGBD.

## Características

✅ **Arquitetura Distribuída**: Middleware para 3+ nós com comunicação via sockets  
✅ **Protocolo de Comunicação**: Sistema de mensagens com checksum MD5 para integridade  
✅ **Eleição de Coordenador**: Algoritmo Bully para eleição automática  
✅ **Heartbeat**: Monitoramento de saúde dos nós  
✅ **Replicação**: Alterações replicadas automaticamente em todos os nós  
✅ **Balanceamento de Carga**: Distribuição round-robin de queries  
✅ **Propriedades ACID**: Controle de transações com commit/rollback  
✅ **Cliente CLI**: Interface simples para executar queries  

## Estrutura do Projeto

```
labsd-atv-02/
├── src/main/java/br/uf/labsd/ddb/
│   ├── Main.java                    # Ponto de entrada do nó
│   ├── client/
│   │   ├── ClientCLI.java          # Interface de linha de comando
│   │   └── DDBClient.java          # Cliente para acesso ao DDB
│   ├── config/
│   │   └── NodeConfig.java         # Configuração dos nós
│   ├── database/
│   │   └── DatabaseManager.java   # Gerenciador MySQL
│   ├── node/
│   │   ├── DDBNode.java           # Nó do DDB
│   │   ├── NetworkManager.java    # Gerenciador de rede
│   │   ├── HeartbeatManager.java  # Gerenciador de heartbeat
│   │   └── ElectionManager.java   # Gerenciador de eleição
│   └── protocol/
│       ├── Message.java            # Mensagens do protocolo
│       └── ChecksumUtil.java       # Utilitário de checksum
├── config/
│   ├── node1.json                  # Configuração do nó 1
│   ├── node2.json                  # Configuração do nó 2
│   ├── node3.json                  # Configuração do nó 3
│   └── setup-mysql.sql             # Script de setup do MySQL
├── pom.xml                         # Configuração Maven
└── README.md
```

## Requisitos

- Java 17+
- Maven 3.6+
- MySQL 8.0+
- 3 instâncias MySQL (podem ser na mesma máquina em portas diferentes ou em máquinas diferentes)

## Configuração

### 1. Configurar MySQL

Para ambiente de teste local, você pode usar Docker para criar 3 instâncias MySQL:

```bash
# Nó 1
docker run -d --name mysql-node1 -p 3307:3306 \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=ddb \
  -e MYSQL_USER=ddb_user \
  -e MYSQL_PASSWORD=ddb_pass \
  mysql:8.0

# Nó 2
docker run -d --name mysql-node2 -p 3308:3306 \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=ddb \
  -e MYSQL_USER=ddb_user \
  -e MYSQL_PASSWORD=ddb_pass \
  mysql:8.0

# Nó 3
docker run -d --name mysql-node3 -p 3309:3306 \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=ddb \
  -e MYSQL_USER=ddb_user \
  -e MYSQL_PASSWORD=ddb_pass \
  mysql:8.0
```

### 2. Configurar Arquivos de Nós

Edite os arquivos em `config/` para apontar para suas instâncias MySQL:

**config/node1.json:**
```json
{
  "nodeId": "node1",
  "host": "localhost",
  "port": 5001,
  "database": {
    "url": "localhost:3307",
    "username": "ddb_user",
    "password": "ddb_pass",
    "database": "ddb"
  },
  "peers": [...]
}
```

### 3. Compilar o Projeto

```bash
mvn clean package
```

## Execução

### Iniciar os Nós DDB

Em terminais separados, inicie cada nó:

```bash
# Terminal 1 - Nó 1
java -jar target/distributed-database-1.0-SNAPSHOT-jar-with-dependencies.jar config/node1.json

# Terminal 2 - Nó 2
java -jar target/distributed-database-1.0-SNAPSHOT-jar-with-dependencies.jar config/node2.json

# Terminal 3 - Nó 3
java -jar target/distributed-database-1.0-SNAPSHOT-jar-with-dependencies.jar config/node3.json
```

### Iniciar o Cliente

```bash
mvn exec:java -Dexec.mainClass="br.uf.labsd.ddb.client.ClientCLI"
```

## Uso do Cliente

O cliente oferece uma interface simples para executar queries:

```sql
ddb> SELECT * FROM users;
ddb> INSERT INTO users (name, email) VALUES ('Carlos', 'carlos@example.com');
ddb> UPDATE users SET name = 'Carlos Silva' WHERE email = 'carlos@example.com';
ddb> DELETE FROM users WHERE id = 1;
```

Cada query mostra:
- O nó que executou a query
- Os resultados formatados em tabela
- Número de linhas afetadas/retornadas

## Protocolo de Comunicação

O sistema usa mensagens JSON com os seguintes tipos:

### Eleição de Coordenador
- `ELECTION`: Inicia processo de eleição
- `ELECTION_OK`: Responde à eleição
- `COORDINATOR`: Anuncia novo coordenador

### Heartbeat
- `HEARTBEAT`: Pulso de vida do nó
- `HEARTBEAT_ACK`: Confirmação de heartbeat

### Replicação
- `QUERY_EXECUTE`: Executa query replicada
- `QUERY_RESULT`: Resultado da query
- `QUERY_COMMIT`: Commita transação
- `QUERY_ROLLBACK`: Reverte transação

### Gerenciamento
- `NODE_JOIN`: Novo nó entra na rede
- `NODE_LEAVE`: Nó sai da rede
- `NODE_STATUS`: Status do nó

## Algoritmos Implementados

### Algoritmo Bully (Eleição)
1. Nó envia ELECTION para nós com ID maior
2. Se recebe OK, espera novo coordenador
3. Se não recebe resposta, torna-se coordenador
4. Anuncia nova coordenação via broadcast

### Replicação
1. Cliente envia query para um nó
2. Nó executa localmente
3. Nó replica via broadcast para peers
4. Peers executam e confirmam
5. Commit em todos os nós

### Detecção de Falhas
1. Heartbeat periódico entre nós
2. Timeout de 3x intervalo de heartbeat
3. Se coordenador falha, nova eleição

## Balanceamento de Carga

O cliente distribui queries usando **round-robin** entre os nós disponíveis, garantindo distribuição uniforme da carga.

## Propriedades ACID

- **Atomicidade**: Transações com commit/rollback
- **Consistência**: Replicação síncrona
- **Isolamento**: Controle de transações MySQL
- **Durabilidade**: Persistência em todos os nós

## Testes

```bash
mvn test
```

## Desenvolvimento Futuro

- [ ] Implementar 2PC (Two-Phase Commit)
- [ ] Adicionar suporte a multicast
- [ ] Implementar sharding de dados
- [ ] Adicionar interface web
- [ ] Métricas e monitoramento
- [ ] Suporte a múltiplos bancos de dados

## Licença

Projeto acadêmico - Universidade Federal

## Autores

Desenvolvido para a disciplina de Sistemas Distribuídos
