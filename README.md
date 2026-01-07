# Usando MySQL para fazer um DDBMS (SGBD Distribuído)

## Pré-requisitos

**Instale o conector do MySQL:**

**code**Bash

```
pip install mysql-connector-python
```

**Crie um banco de dados chamado** **dist_db** **e uma tabela de teste em** **todas** **as máquinas (nós):**

**code**SQL

```
CREATE DATABASE dist_db;
USE dist_db;
CREATE TABLE usuarios (id INT AUTO_INCREMENT PRIMARY KEY, nome VARCHAR(100), email VARCHAR(100));
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

* **Configuração de Rede:**

  * **Certifique-se de que o MySQL está rodando e a tabela em `dist_db.sql` foi criada.**
  * **Se for testar em uma única máquina, abra 3 terminais.**
* **Iniciar os Nós:**

  * **Terminal 1:** **python middleware.py 1**
  * **Terminal 2:** **python middleware.py 2**
  * **Terminal 3:** **python middleware.py 3**
* **Observar:**

  * **Você verá logs como** **[*] Nó 3 iniciado...** **e** **[*] EU SOU O NOVO LÍDER (Nó 3)** **(pois 3 é o maior ID).**
  * **Verá logs de Heartbeat periodicamente.**
* **Executar Cliente:**

  * **Terminal 4:** **python client.py**
  * **Digite:** **INSERT INTO usuarios (nome, email) VALUES ('Joao', 'joao@teste.com');**

    * **O middleware receberá, verá que é escrita, mandará para o líder (Nó 3), que replicará para 1 e 2.**
  * **Digite:** **SELECT * FROM usuarios;**

    * **O middleware (randomicamente escolhido pelo cliente) responderá diretamente com os dados locais.**
* **Teste de Falha e Eleição:**

  * **Mata o processo do** **Nó 3** **(Ctrl+C).**
  * **Aguarde 5-10 segundos.**
  * **Os nós 1 e 2 detectarão a falta de heartbeat do 3.**
  * **O Nó 2 (próximo maior ID) iniciará a eleição e se declarará Líder.**
  * **Tente fazer um INSERT pelo cliente. O sistema deve continuar funcionando, agora roteando para o Nó 2.**
