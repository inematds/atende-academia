# Estado — atualizado 2026-10-19, ciclo 3

## Funciona
- Base HTTP concorrente em 127.0.0.1, PORTA=<n>, auth, JSON UTF-8, SQLite/WAL e semente única; alunos/planos/matrículas e aulas/reservas/espera do ciclo anterior preservados.
- Check-in por código: matrícula ativa, código inexistente 404, um por aluno/dia com mesmo id/horário no segundo pedido; listagem por período/aluno, nome atual e ordem por quando/id. Não consome créditos.
- Tarefas locais: presença/falta ao término gravado na reserva; avisos de vencimento uma vez por matrícula; reativação com consentimento, 14 dias inclusivos e comparação estrita da mensagem com o último check-in. Tudo persiste.
- Relógio de tarefas recebido em agora vale apenas para a rodada e grava o horário correto nas mensagens. nao_contatar impede criação de avisos. Lembretes de avaliação preparados, ainda dependentes do módulo de avaliação.
- Versão 0.3.0. Novo domínio src/attendance.py sob a transação/trava do dispatcher; Classes.message aceita instante explícito.
- Suíte completa: **26 passed / 73 failed**; pytest-ciclo-3.log. Seis testes adicionais passam. Verificador: **LIMITES OK** (hash a768b39fe2101c18, 99 testes).
- Verificação HTTP adicional: 10 check-ins simultâneos → um 201 + nove 200 com mesmo id; fronteira do vencimento, idempotência, nao_contatar e isolamento do relógio aprovados.

## Falta
- Biblioteca/ficha/meu treino; 12 SVGs CSS manuais e páginas; avaliação física e verificação integrada de seus lembretes.
- Conversa completa na ordem §11, inclusive check-in, parar, confirmação de oferta e treino do dia. Teste de vencimento ainda para no chat parar, ausente; não criar atalho fora da ordem.
- Reenvio pendente no início das tarefas depende da Evolution: reenviadas permanece zero no modo simulado atual. Integrações somente com servidores falsos.
- Campanhas, LGPD, Raio-X, cadastros restantes/backup; Evolution/Telegram; Docker/.env.exemplo/README Deploy na VPS/render-exercicios e páginas / e /equipe.
- Ainda não concluído: 73 falhas por funcionalidades pendentes. Nenhum conflito teste/spec identificado neste ciclo.

## Como retomar
1. Ler goal → state → plan → canal → fim de progress/failures; spec completa e conftest já lidos neste ciclo.
2. Implementar biblioteca/ficha e seleção do treino do dia (§6), depois SVGs/páginas (§7) e avaliação (§8). Deixar envio do treino pelo chat para o dispatcher completo da seção 11.
3. Reutilizar Attendance.checkin, Classes.reserve/change e Classes.message; conectar reenvio real simulado pela Evolution no início de Attendance.run quando chegar à integração.
4. Rodar suíte inteira para arquivo (tail -n 30), verificar-limites e atualizar registros; sem commit/rede externa e sem executar render-exercicios.
