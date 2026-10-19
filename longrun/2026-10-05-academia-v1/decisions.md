# Decisões (só acrescentar)

| data | decisão | motivo | alternativa descartada |
|---|---|---|---|
| 2026-10-19 | SQLite com documentos JSON por entidade, chave composta coleção/id e sequências persistentes | permite evoluir entidades sem reconstruir a base; transação abrange toda operação HTTP e RLock serializa acesso compartilhado | estado apenas em memória ou arquivo JSON sem transação |
| 2026-10-19 | Separar store.py, domain.py e server.py; não criar respostas fictícias para rotas futuras | checkpoint verificável da base, reutilização das regras na futura conversa | implementar stubs que retornam listas vazias para passar verificações superficiais |

| 2026-10-19 13:54 -0300 | Guardar matricula_id, fim e modalidade na reserva e usar Classes sob a transação HTTP existente | devolver crédito à matrícula consumida e preservar dados da reserva; mesma regra reutilizável no chat | selecionar matrícula atual ao devolver crédito ou duplicar regras no transporte |

| 2026-10-19 13:56 -0300 | Attendance separado, relógio explícito por rodada e fim persistido da reserva para presença automática | preservar isolamento do relógio e aulas já reservadas após edição da grade; reutilizar trava HTTP e caixa de saída | alterar ambiente/global do relógio ou recalcular término usando grade editada |
