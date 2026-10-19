# Falhas (só acrescentar; ao fim, a menor correção vira linha no FALHAS.md do projeto)

| data | o que quebrou | tentativa | resultado | prompt \| infra |
|---|---|---|---|---|
| 2026-10-19 | Leitura inicial tentou tests/test_base.py inexistente | localizar com rg --files e ler tests/test_basico.py | leitura corrigida, sem alteração de testes | prompt |
| 2026-10-19 | Suíte completa: 90 failed, funcionalidades ainda ausentes | implementar base/alunos/planos/matrículas primeiro | 9 passed, 90 failed; próximas rotas no plan.md, sem conflito identificado entre contrato e testes | infra |
| 2026-10-19 | Escrita de FALHAS.md substituiu histórico | recuperar HEAD e inserir novos registros no topo | histórico preservado antes do fim do ciclo | prompt |

| 2026-10-19 13:54 -0300 | Suíte ainda com 79 falhas por módulos ausentes; aulas depende de chat e check-in/tarefas | implementar domínio de aulas e rodar suíte completa | 20 passed / 79 failed; pendências registradas, sem conflito teste/spec identificado | infra |
