# Canal — academia-v1 (só acrescentar; nunca reescrever)

Conhecimento do projeto que a compactação perde: fatos descobertos, aprendizados, glossário, armadilhas, onde estão as coisas.
Não é estado da tarefa (isso vai em state/plan/progress). Preencha cedo — o hook avisa na faixa 1 (~50% do contexto).

Formato: `- AAAA-MM-DD HH:MM · fato|aprendizado|glossário|armadilha · texto`

- 2026-10-19 13:50 · fato · Primeira leitura completa da especificação e tests/conftest.py feita. Estado anterior era apenas planejamento; agora há implementação inicial.
- 2026-10-19 13:50 · fato · Store.save/next_id precisam executar dentro de `with store.lock, store.db` (já feito no dispatcher); exceções desfazem a transação. Semente usa marcador em metadados, não contagem de entidades.
- 2026-10-19 13:50 · armadilha · Testes de alunos e base atravessam módulos: deduplicação exige /dados, autenticação exige rotas públicas completas, persistência exige reservas, semente exige desativação de exercícios. Nove testes passam neste checkpoint, sem completar essas dependências artificialmente.
- 2026-10-19 13:50 · fato · Academia.ativa(aluno_id, data ISO) já centraliza escolha de matrícula e prioridade dos motivos de recusa para futuras reservas/check-in. Integrações e webhooks ainda não implementados.

- 2026-10-19 13:54 -0300 · fato · Classes implementa ocorrências/reservas/cancelamentos/espera, sob store.lock + store.db do dispatcher; matricula_id é a matrícula que consumiu o crédito.
- 2026-10-19 13:54 -0300 · armadilha · §4.4 cita oferta também no cancelamento pela academia (§4.6): implementado literalmente; confirmar depois tenta reservar pelas regras normais e ocorrência cancelada recusa sem_aula.
- 2026-10-19 13:54 -0300 · fato · 20 passed / 79 failed e LIMITES OK. Restam em aulas os testes que atravessam chat e check-in/tarefas; caixa de saída é simulada até implementação da Evolution.
