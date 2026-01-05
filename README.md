# Usando MySQL para fazer um DDBMS (SGBD Distribuído)

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
