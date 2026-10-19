# Estado — ciclo 6

## Funciona
- Base HTTP concorrente, autenticação, JSON, SQLite/WAL e semente única; alunos/planos/matrículas, aulas/reservas/espera/créditos, check-in e tarefas locais.
- Catálogo e fichas persistentes, seleção do treino por check-ins; 12 SVGs CSS e páginas/arquivos públicos com caminhos restritos.
- Avaliação física em src/evaluations.py: candidatos por janela/passo/duração, antecedência e feriados, professor ativo, conflitos semiabertos com aulas e avaliações ativas, escolha automática por id, agendamento serializado, cancelamento, resultados protegidos e listagem ordenada.
- Lembretes de avaliação já conectados ao Attendance. Verificação HTTP adicional passou: dez pedidos concorrentes geram um 201 e nove 409; resultados exigem token; persistem após reinício; horários adjacentes permitidos; lembretes respeitam fronteira de 24h, idempotência e nao_contatar.
- Versão 0.6.0. Suíte completa: **45 passed / 54 failed** em 18.85s (pytest-ciclo-6.log). **LIMITES OK**, hash a768b39fe2101c18 e 99 testes preservados.

## Falta
- Conversa completa (§11), na ordem definida, incluindo fluxos persistentes e fila humana; nenhum chat parcial implementado.
- Testes de avaliação que atravessam /dados, exclusão e conversa permanecem pendentes desses módulos; resultados não são expostos por rota pública.
- Reenvio nas tarefas, campanhas, LGPD, Raio-X, cadastros restantes/backup, Evolution e Telegram com servidores falsos.
- Docker/.env.exemplo/README Deploy na VPS; tools/render-exercicios (escrever, sem executar); páginas / e /equipe.
- Não concluído: 54 falhas por funcionalidades pendentes. Nenhum conflito entre teste e especificação identificado.

## Como retomar
1. Ler goal → state → plan → canal → fim de progress/failures. Especificação completa e tests/conftest.py lidos neste ciclo.
2. Implementar conversa conforme ordem exata do §11, reutilizando Training, Attendance, Classes e Evaluations; resultados de avaliação nunca entram no chat.
3. Operações de Evaluations dependem da transação e trava já usadas pelo dispatcher. Conflitos de aulas consideram também o dia anterior para aulas que cruzem meia-noite; ocorrências canceladas não bloqueiam o professor.
4. Rodar pytest completo para arquivo e ler tail -n 30; verificar limites e atualizar registros. Sem commit, API externa, instalação ou execução do render.
