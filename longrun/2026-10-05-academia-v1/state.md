# Estado — ciclo 7

## Funciona
- Base HTTP concorrente, auth/JSON, SQLite/WAL e semente única; alunos/planos/matrículas, aulas/reservas/espera/créditos, check-in e tarefas locais.
- Catálogo/fichas e treino do dia; 12 SVGs CSS e páginas/arquivos públicos restritos; avaliação física com agenda/conflitos/resultados privados.
- Conversa local (§11) em src/conversation.py: prioridade de saúde, opt-out, humano, fluxos persistentes de reserva/cancelamento, confirmação da espera, cadastro, check-in, avaliação, aulas, plano, treino, exercícios e FAQ, escalada após dois erros.
- Fila humana local com responder/encerrar e suspensão do bot exceto saúde (§21); histórico de entradas/respostas e estado por telefone persistidos.
- Verificação HTTP adicional passou: reserva iniciada antes do reinício e confirmada depois; fila suspende bot; saúde eleva prioridade; encerramento retoma bot; check-in normalizado e telefone inválido.
- Versão 0.7.0. Suíte: **63 passed / 36 failed** em 54.13s (pytest-ciclo-7.log); **LIMITES OK**, hash a768b39fe2101c18 e 99 testes preservados.

## Falta
- Reenvio das tarefas, campanhas, LGPD (/dados e anonimização), Raio-X, cadastros restantes e backup.
- Evolution/sendMedia e Telegram (incluindo avisos de reserva/cancelamento e repasse de mensagens humanas), exclusivamente contra servidor falso.
- Docker/.env.exemplo/README Deploy na VPS; tools/render-exercicios (escrever, não executar); páginas / e /equipe.
- O teste de opt-out da conversa chega à leitura de /dados, ainda ausente. 36 falhas restantes; não concluído. Nenhum conflito teste/spec identificado.

## Como retomar
1. Ler goal → state → plan → canal → fim de progress/failures. Especificação e conftest lidos neste ciclo.
2. Continuar tarefas/campanhas/LGPD: histórico direto está em mensagens; automáticas e respostas humanas em saida. Exportação deve reunir os dois sem duplicar. Anonimização deve limpar conversas/atendimentos do telefone antigo além dos dados de domínio.
3. Conversation.receive usa a transação do dispatcher. conversas é indexado por telefone; atendimentos guarda fila; mensagens guarda histórico. Integrações ainda não estão ligadas.
4. Rodar pytest para arquivo, ler tail -n 30; verificar limites e atualizar registros. Sem commit, API externa, instalação ou render.
