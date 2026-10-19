# Falhas (só acrescentar; ao fim, a menor correção vira linha no FALHAS.md do projeto)

| data | o que quebrou | tentativa | resultado | prompt \| infra |
|---|---|---|---|---|
| 2026-10-19 | Leitura inicial tentou tests/test_base.py inexistente | localizar com rg --files e ler tests/test_basico.py | leitura corrigida, sem alteração de testes | prompt |
| 2026-10-19 | Suíte completa: 90 failed, funcionalidades ainda ausentes | implementar base/alunos/planos/matrículas primeiro | 9 passed, 90 failed; próximas rotas no plan.md, sem conflito identificado entre contrato e testes | infra |
| 2026-10-19 | Escrita de FALHAS.md substituiu histórico | recuperar HEAD e inserir novos registros no topo | histórico preservado antes do fim do ciclo | prompt |

| 2026-10-19 13:54 -0300 | Suíte ainda com 79 falhas por módulos ausentes; aulas depende de chat e check-in/tarefas | implementar domínio de aulas e rodar suíte completa | 20 passed / 79 failed; pendências registradas, sem conflito teste/spec identificado | infra |

| 2026-10-19 13:56 -0300 | Suíte ainda com módulos ausentes (chat, exercícios, avaliação, integrações e entrega) | implementar check-in/reativação e núcleo local de tarefas | 26 passed / 73 failed; sem conflito teste/spec; próximos módulos no plan.md | infra |

| 2026-10-19 | Verificação manual recebeu 401 usando token do fixture com configuração de exemplo | repetir copiando fixture para dados temporários | erro de preparação corrigido, sem alterar implementação | prompt |

| 2026-10-19 14:00 -0300 | Suíte ainda com módulos ausentes, inclusive SVG e chat que atravessam treino | implementar catálogo/ficha e seleção do treino | 28 passed / 71 failed; nenhum conflito teste/spec identificado | infra |
