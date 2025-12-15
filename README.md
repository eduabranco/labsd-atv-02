- Vamos usar MySQL para fazer um DDBMS (DBMS Distribuído)

## Nome da Tarefa: Bando de Dados Distribuídos

## Descrição:

Desenvolver um middleware para disponibilizar um banco de dados distribuídos baseado no SGBD MySQL. O middleware deverá ser desenvolvido baseado nas seguintes premissas:

1. Pode ser desenvolvido em qualquer linguagem de programação;
2. Deverá ser executado em pelo menos 03 máquinas diferentes;
3. Usar o SGBD MySQL;
4. A comunicação entre os nós do banco de dados distribuídos deverá ocorrer através de sockets;
5. Desenvolver protocolo para troca de informações entre as diversas máquinas;
6. Possibilidade de configurar os nós do DDB através de IPs de cada máquina;
7. O DDB deverá seguir as premissas de uma DDM homogêneo autônomo;
8. Todas as alterações efetuadas em um dos nós do DDB deverá ser replicada em todos os outros nós da rede;
9. Preferencialmente poderá ter um coordenador. Porém, caso o coordenador falhe, deverá ter algum algoritmo para a eleição de um novo coordenador;
10. O tipo de comunicação deverá ser determinado: broadcast, unicast, multicast;
11. Garantir que as operações sigam as propriedades ACID;
12. Todos os nós do DDB deverão informar periodicamente que estão ativos no DDB;
13. Usar um mecanismo do tipo checksum para verificar a integridade dos dados recebidos;
14. Garantir que não haja sobrecarga de nós no DDB, ou seja, que as requisições possam ser distribuídas entre os nós da rede;
15. Cada nó deverá infomar as queries que foram requisitadas para ele e informar o conteúdo que será transmitido;
16. Para acessar o DDB deverá ser criada uma aplicação com interface simples para executar queries. Cada retorno de queries deverá informar o resultado e o nó do DDB em que foi executada.
