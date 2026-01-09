# Usando MySQL para fazer um DDBMS (SGBD Distribuído)

## Pré-requisitos

### 1. Instalar Dependências Python

```bash
pip install mysql-connector-python
```

### 2. Configuração do MySQL (NOVO - Automático!)

Este projeto agora suporta **múltiplas configurações de MySQL** automaticamente:
- Root sem senha
- Root com senha 'password'
- Root com qualquer outra senha
- Usuários personalizados

**Método Recomendado: Usar o script de configuração automática**

Execute em **CADA NÓ** do sistema distribuído:

```bash
python3 db_setup.py
```

O script irá:
1. ✅ Detectar automaticamente sua configuração MySQL
2. ✅ Criar o banco de dados `dist_db`
3. ✅ Criar a tabela `usuarios`
4. ✅ (Opcional) Criar um usuário dedicado `ddb_user` para segurança
5. ✅ Gerar arquivo `config_db.py` com as credenciais corretas

**Método Alternativo: Configuração Manual**

Se preferir configurar manualmente, execute:

```sql
CREATE DATABASE dist_db;
USE dist_db;
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY, 
    nome VARCHAR(100), 
    email VARCHAR(100)
);

-- Opcional: Criar usuário dedicado (recomendado)
CREATE USER 'ddb_user'@'localhost' IDENTIFIED BY 'ddb_pass';
GRANT ALL PRIVILEGES ON dist_db.* TO 'ddb_user'@'localhost';
FLUSH PRIVILEGES;
```

Depois configure as credenciais via:
- **Opção 1:** Copie `.env.example` para `.env` e edite as credenciais
- **Opção 2:** Use variáveis de ambiente:
  ```bash
  export MYSQL_USER=ddb_user
  export MYSQL_PASSWORD=ddb_pass
  ```

---

## Arquitetura da Solução

* **Topologia:** **Peer-to-Peer com um Líder (Coordenador) dinâmico.**
* **Comunicação:** **Sockets TCP (para confiabilidade).**
* **Protocolo:** **Mensagens JSON contendo cabeçalhos (tipo, origem) e payload, assinadas com MD5 (Checksum).**
* **Consistência (ACID):** **Implementação simplificada do** **Two-Phase Commit (2PC)**. O Líder recebe a escrita, solicita "Prepare" a todos, se todos derem OK, envia "Commit".
* **Eleição:** **Algoritmo** **Bully** **(o nó com maior ID/IP ativo assume se o líder falhar).**
* **Banco de Dados:** **MySQL (cada nó tem sua instância local).**

---

## Como Testar

### **1. Configuração de Rede:**

* **Teste Local (1 máquina, 3 processos):**
  * Configure IPs em [config.py](config.py) para localhost:
    ```python
    NODES = {
        1: ('127.0.0.1', 5001),
        2: ('127.0.0.1', 5002),
        3: ('127.0.0.1', 5003)
    }
    ```

* **Teste Distribuído (múltiplas máquinas):**
  * Pegue o IP de cada máquina: `ip a` ou `ifconfig`
  * Configure em [config.py](config.py):
    ```python
    NODES = {
        1: ('192.168.1.10', 5001),  # Máquina 1
        2: ('192.168.1.11', 5002),  # Máquina 2
        3: ('192.168.1.12', 5003)   # Máquina 3
    }
    ```
  * Execute `python3 db_setup.py` em **CADA** máquina

### **2. Iniciar os Nós:**

Abra um terminal para cada nó:

* **Terminal 1:** 
  ```bash
  python middleware.py 1
  ```
* **Terminal 2:** 
  ```bash
  python middleware.py 2
  ```
* **Terminal 3:** 
  ```bash
  python middleware.py 3
  ```

### **3. Observar Logs:**

Você verá mensagens como:
```
[*] Using database configuration from config_db.py
[*] Nó 3 iniciado em 192.168.1.12:5003
[*] Líder Atual: 3
[*] EU SOU O NOVO LÍDER (Nó 3)
```

O nó com maior ID (3) será eleito líder automaticamente.

### **4. Executar Cliente:**

Em um novo terminal:

```bash
python client.py
```

**Comandos de Teste:**

```sql
-- Inserir dados (replicado em todos os nós)
SQL> INSERT INTO usuarios (nome, email) VALUES ('João', 'joao@teste.com');
[Sucesso] Executado no Nó: 3

-- Consultar dados (leitura local distribuída)
SQL> SELECT * FROM usuarios;
[Sucesso] Executado no Nó: 2
Dados: [{'id': 1, 'nome': 'João', 'email': 'joao@teste.com'}]

-- Atualizar dados
SQL> UPDATE usuarios SET email = 'joao.silva@teste.com' WHERE id = 1;

-- Deletar dados
SQL> DELETE FROM usuarios WHERE id = 1;
```

### **5. Teste de Falha e Eleição:**

1. **Mate o processo do Nó 3** (líder atual):
   ```
   Ctrl+C no terminal do Nó 3
   ```

2. **Aguarde 5-10 segundos**

3. Observe os logs nos outros nós:
   ```
   [!] Líder inativo detectado. Iniciando Eleição (Bully)...
   [*] EU SOU O NOVO LÍDER (Nó 2)
   ```

4. **Teste que o sistema continua funcionando:**
   ```sql
   SQL> INSERT INTO usuarios (nome, email) VALUES ('Maria', 'maria@teste.com');
   [Sucesso] Executado no Nó: 2
   ```

O sistema agora roteia automaticamente para o novo líder (Nó 2)!

---

## Solução de Problemas

### Erro de Conexão MySQL

Se você ver erros como:
```
mysql.connector.errors.ProgrammingError: Access denied for user 'root'@'localhost'
```

**Solução:** Execute `python3 db_setup.py` - ele detectará automaticamente a configuração correta.

### Nós não se comunicam

1. Verifique se os IPs em [config.py](config.py) estão corretos
2. Teste conectividade: `ping <IP_DO_NÓ>`
3. Verifique firewall: `sudo ufw allow 5001:5003/tcp`
4. Verifique se as portas estão livres: `netstat -tuln | grep 500`

### Banco de dados não sincroniza

1. Verifique se **todos** os nós executaram `db_setup.py`
2. Confirme que todos usam o mesmo banco de dados `dist_db`
3. Verifique logs de replicação nos terminais dos nós

---

## Arquivos do Projeto

| Arquivo | Descrição |
|---------|-----------|
| [middleware.py](middleware.py) | Servidor de nó distribuído (replicação, eleição, heartbeat) |
| [client.py](client.py) | Cliente para enviar queries SQL |
| [config.py](config.py) | Configuração de nós e banco de dados |
| [db_setup.py](db_setup.py) | **NOVO!** Script automático de configuração MySQL |
| [dist_db.sql](dist_db.sql) | Schema SQL (uso manual opcional) |
| `.env.example` | Exemplo de variáveis de ambiente |

---

## Recursos Avançados

### Variáveis de Ambiente

Você pode configurar o banco via ambiente ao invés de `config_db.py`:

```bash
export MYSQL_USER=meu_usuario
export MYSQL_PASSWORD=minha_senha
export MYSQL_DATABASE=dist_db
python middleware.py 1
```

### Prioridade de Configuração

1. **config_db.py** (gerado por `db_setup.py`) - Mais alta
2. **Variáveis de ambiente** (.env ou export)
3. **Valores padrão** - Mais baixa


