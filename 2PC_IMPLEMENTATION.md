# Implementação do Two-Phase Commit (2PC)

## Visão Geral

O protocolo Two-Phase Commit (2PC) foi implementado completamente para garantir as propriedades ACID em transações distribuídas.

## Arquitetura do 2PC

### Fase 1: PREPARE (Preparação)

1. **Coordenador (Líder)** recebe uma operação de escrita
2. Coordenador envia mensagem `PREPARE` com a query para todos os nós participantes
3. Cada **Participante**:
   - Valida se pode executar a query
   - Executa a query SEM commitar (mantém em transação pendente)
   - Responde `VOTE_YES` se sucesso, `VOTE_NO` se falha
4. Coordenador coleta todos os votos

### Fase 2: COMMIT ou ABORT (Decisão)

**Se todos votaram YES:**
- Coordenador envia mensagem `COMMIT` para todos
- Cada nó executa `db.commit()` confirmando a transação
- Todos os dados são persistidos

**Se algum votou NO:**
- Coordenador envia mensagem `ABORT` para todos
- Cada nó executa `db.rollback()` revertendo a transação
- Nenhum dado é alterado (atomicidade garantida)

## Implementação no Código

### Novas Mensagens do Protocolo

```python
# Fase 1
{'type': 'PREPARE', 'payload': {'query': 'INSERT INTO ...'}}
{'type': 'VOTE_YES', 'node': 1}  # Resposta positiva
{'type': 'VOTE_NO', 'msg': 'erro', 'node': 1}  # Resposta negativa

# Fase 2
{'type': 'COMMIT', 'payload': {}}
{'type': 'ABORT', 'payload': {}}
```

### Funções Principais

#### `handle_prepare(query)`
- Valida e prepara a query sem commitar
- Armazena em `self.pending_transaction`
- Retorna `VOTE_YES` ou `VOTE_NO`

#### `handle_commit()`
- Executa `db.commit()` na transação pendente
- Limpa `self.pending_transaction`

#### `handle_abort()`
- Executa `db.rollback()` revertendo mudanças
- Limpa `self.pending_transaction`

#### `execute_2pc(query)`
- Coordena todo o protocolo 2PC
- Gerencia Fase 1 (PREPARE) e Fase 2 (COMMIT/ABORT)

## Garantias ACID

### ✅ Atomicidade
- Transação é commitada em TODOS os nós ou em NENHUM
- Rollback automático em caso de falha

### ✅ Consistência
- Validação antes de commitar garante integridade
- Constraints do MySQL são verificados na fase PREPARE

### ✅ Isolamento
- `transaction_lock` evita condições de corrida
- MySQL garante isolamento de transações

### ✅ Durabilidade
- Commit do MySQL persiste dados em disco
- Apenas após COMMIT é garantida a durabilidade

## Exemplo de Execução

```
Cliente envia: INSERT INTO usuarios VALUES (1, 'João', 'joao@email.com')

=== FASE 1: PREPARE ===
Líder (Nó 3):
  [*] [2PC-FASE-1] Enviando PREPARE para todos os nós
  [*] Preparação local: VOTE_YES
  
Nó 2:
  [*] [2PC-PREPARE] Validando query: INSERT INTO ...
  [*] [2PC-PREPARE] VOTE_YES - Query válida
  
Nó 1:
  [*] [2PC-PREPARE] Validando query: INSERT INTO ...
  [*] [2PC-PREPARE] VOTE_YES - Query válida

Líder (Nó 3):
  [*] [2PC-DECISÃO] Votos: 3 YES, 0 NO -> COMMIT

=== FASE 2: COMMIT ===
Líder (Nó 3):
  [*] [2PC-FASE-2] Enviando COMMIT para todos os nós
  [*] [2PC-COMMIT] Commitando transação
  
Nó 2:
  [*] [2PC-COMMIT] Commitando transação
  [*] [2PC-COMMIT] Transação confirmada com sucesso
  
Nó 1:
  [*] [2PC-COMMIT] Commitando transação
  [*] [2PC-COMMIT] Transação confirmada com sucesso

Líder (Nó 3):
  [*] [2PC-COMPLETO] Transação commitada em 3 nós: [3, 2, 1]

Cliente recebe:
  [Sucesso] 2PC completo. Commitado em 3 nós
```

## Exemplo de Abort

```
Cliente envia: INSERT INTO usuarios VALUES (999, NULL, 'email@email.com')
# NULL viola constraint NOT NULL

=== FASE 1: PREPARE ===
Nó 2:
  [!] [2PC-PREPARE] VOTE_NO - Erro: Column 'nome' cannot be null

Líder (Nó 3):
  [*] [2PC-DECISÃO] Votos: 2 YES, 1 NO -> ABORT

=== FASE 2: ABORT ===
Todos os nós:
  [*] [2PC-ABORT] Abortando transação
  [*] [2PC-ABORT] Transação revertida

Cliente recebe:
  [Erro] Transação abortada. Nós com falha: [2]
```

## Tratamento de Falhas

### Nó Inativo Durante PREPARE
- Não participa da votação
- Sincronização posterior via heartbeat

### Nó Falha Após VOTE_YES
- Coordenador procede com COMMIT
- Nó recupera dados na reconexão

### Coordenador Falha
- Novo líder eleito via algoritmo Bully
- Transações pendentes são abortadas (timeout)

## Configuração

O 2PC é ativado automaticamente com:
- `db.autocommit = False` - Permite transações manuais
- `transaction_lock` - Sincronização de threads

## Diferenças da Implementação Anterior

| Aspecto | Antes (Simplificado) | Agora (2PC Completo) |
|---------|---------------------|----------------------|
| Validação | Apenas no líder | Em todos os nós (PREPARE) |
| Atomicidade | Melhor esforço | Garantida (ABORT em falha) |
| Rollback | Não implementado | Completo (db.rollback()) |
| Fases | 1 fase (REPLICATE) | 2 fases (PREPARE + COMMIT) |
| ACID | Parcial | Completo ✅ |

## Referências

- [Two-Phase Commit Protocol - Wikipedia](https://en.wikipedia.org/wiki/Two-phase_commit_protocol)
- [MySQL Transactions](https://dev.mysql.com/doc/refman/8.0/en/commit.html)
- Gray, J. (1978). "Notes on Data Base Operating Systems"
