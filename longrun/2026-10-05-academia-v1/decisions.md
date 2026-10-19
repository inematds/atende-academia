# Decisões (só acrescentar)

| data | decisão | motivo | alternativa descartada |
|---|---|---|---|
| 2026-10-19 | SQLite com documentos JSON por entidade, chave composta coleção/id e sequências persistentes | permite evoluir entidades sem reconstruir a base; transação abrange toda operação HTTP e RLock serializa acesso compartilhado | estado apenas em memória ou arquivo JSON sem transação |
| 2026-10-19 | Separar store.py, domain.py e server.py; não criar respostas fictícias para rotas futuras | checkpoint verificável da base, reutilização das regras na futura conversa | implementar stubs que retornam listas vazias para passar verificações superficiais |
