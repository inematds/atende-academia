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

- 2026-10-19 13:56 -0300 · fato · Attendance.checkin/listing/run em src/attendance.py; tasks grava quando com instante da rodada via Classes.message(..., instant). Reativação compara mensagem > último check-in (não >=); presença usa fim persistido da reserva. Reenvio ainda falta; lembretes de avaliação preparados mas sem API de avaliação. Suíte 26 passed / 73 failed, LIMITES OK; check-in concorrente adicional aprovado.

- 2026-10-19 14:00 -0300 · fato · Training em src/training.py fornece catálogo/ficha/today; today conta datas distintas de check-in anteriores a hoje, verifica plano primeiro e permite exercício desativado em ficha existente. Store.delete remove por coleção/id. Nenhum SVG criado neste ciclo; svg=false é real. Suíte 28 passed / 71 failed, LIMITES OK.

- 2026-10-19 14:04 -0300 · fato · Ciclo 5: src/exercise_pages.py fornece Resource e file_path (resolve + parent evita symlink externo); handler preserva MIME de HTML/SVG/MP4. 12 SVGs têm CSS d:path para articulações e transform para cabeça/equipamento. Pytest 43/99, LIMITES OK. Movimento no navegador não conferido; render não executado. tools/render-exercicios ainda pendente.

- 2026-10-19 14:07 -0300 · fato · Ciclo 6: Evaluations em src/evaluations.py; agenda/resultados privados funcionam, lembretes usam Attendance existente. 45 passed / 54 failed e LIMITES OK. HTTP adicional provou concorrência 1/10, auth, persistência, adjacência, lembrete/opt-out. Testes transversais de avaliação aguardam conversa e LGPD; próxima etapa é §11 inteiro.

- 2026-10-19 14:11 -0300 · fato · Ciclo 7: Conversation em src/conversation.py; conversas por telefone, atendimentos para fila, mensagens para entradas/respostas diretas. /saida mantém automáticas/humano. LGPD deve combinar históricos e apagar estado do telefone antigo. 63 passed / 36 failed e LIMITES OK; testes de integração agora esperam avisos ausentes e suíte levou 54s. Fluxo confirmado após reinício por HTTP; sem chamadas externas.

- 2026-10-19 14:15 -0300 · fato · Ciclo 8: src/privacy.py implementa campanhas e LGPD; src/raiox.py API/CLI mensal. 74 passed / 25 failed, foco 8 passed, LIMITES OK. Anonimização mantém aluno_id nas mensagens vazias e remove telefone, conversa e identificação da fila; futuro reenvio precisa ignorar telefone=None. Raio-X usa situacao interna da matrícula, não status calculado. Sem rede externa.

- 2026-10-19 14:20 -0300 · fato · Ciclo 9: src/catalogs.py cobre professores/grade/FAQ/modalidades/salas; src/backup.py usa SQLite backup + ZIP com configuração, restaura somente com servidor parado. 78 passed / 21 failed, foco cadastros 6 passed, LIMITES OK. HTTP extra conferiu auth, rollback de horário inválido e restauração em diretório novo. Restam integrações e entrega; nenhum render/rede externa/commit.

- 2026-10-19 14:25 -0300 · fato · Ciclo 10: src/evolution.py implementa webhook/send/deliver/retry; Conversation.receive(whatsapp=True) envia apenas respostas do webhook. Ids recebidos persistem em evolution_recebidas. retry respeita opt-out de automáticas e ignora anonimização. 84 passed / 15 failed, foco Evolution 7 passed, LIMITES OK; Telegram e entrega pendentes. Nenhuma rede externa/render/commit.

- 2026-10-19 · fato · Retomada pelo Claude após ciclo 11 interrompido: src/telegram.py (send síncrono, timeout 3 s, sem redirect; ids das mensagens por atendimento em `telegram_ids`, resposta em cima casa qualquer um deles). /webhook/telegram exige X-Telegram-Bot-Api-Secret-Token (401) antes do corpo. Avisos "Nova reserva:"/"Cancelada:" saem de Conversation.reserve e do fluxo de cancelar.
- 2026-10-19 · armadilha · test_dockerfile procura "pip install" no Dockerfile inteiro, inclusive comentários. .env.exemplo não pode ter "http" nem em comentário.
- 2026-10-19 · fato · verificar-independente: movimento chromium 3/3, docker ok, hyperframes PULADO (pacote não instalado; `npm install hyperframes` é do humano).
