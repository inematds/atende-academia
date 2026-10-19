# Estado — ciclo 9

## Funciona
- Base HTTP concorrente, auth/JSON, SQLite/WAL, semente única; alunos/planos/matrículas, aulas/reservas/espera/créditos, check-in e tarefas locais.
- Catálogo/fichas e treino do dia; 12 SVGs CSS e páginas/arquivos públicos restritos; avaliação física com agenda/conflitos/resultados privados.
- Conversa local persistente (§11), fila humana local, suspensão do bot exceto saúde, histórico por telefone.
- Campanhas com consentimento/opt-out/trava, exportação e anonimização LGPD, Raio-X mensal API/CLI com mesclagem do acompanhamento.
- Cadastros (§18): professores, grade, FAQ, modalidades e salas; professores/grade desativados preservam reservas e avaliações existentes. Alterações entram na conversa/agenda imediatamente.
- Backup online consistente via sqlite3.Connection.backup e arquivo ZIP com academia.json; restauração com servidor parado valida banco/configuração e recupera também em diretório novo.
- Versão 0.9.0. Suíte completa: **78 passed / 21 failed** em 55.22s (pytest-ciclo-9.log); foco cadastros: **6 passed**. **LIMITES OK**, 99 testes e contrato preservados.
- HTTP adicional verificou auth, duplicidade, validação/rollback de horários, novos cadastros e restauração em diretório novo com configuração preservada.

## Falta
- Evolution/sendMedia/reenvio e Telegram, incluindo avisos pelo chat e repasse de mensagens humanas; testar exclusivamente contra servidor falso.
- Docker/.env.exemplo/README Deploy na VPS; tools/render-exercicios (escrever, não executar); páginas / e /equipe.
- 21 falhas restantes por integrações e entrega ausentes; não concluído. Nenhum conflito teste/spec identificado.

## Como retomar
1. Ler goal → state → plan → canal → fim de progress/failures. Especificação inteira e conftest lidos neste ciclo.
2. Implementar Evolution e reenvio antes das demais tarefas; depois Telegram. Mensagens diretas estão em mensagens; automáticas/humano em saida. Anonimização deixa telefone=None e texto vazio: nunca reenviar essas mensagens.
3. src/catalogs.py usa a transação do dispatcher. src/backup.py é CLI independente de Store (restauração não semeia antes de recuperar). Servidor deve estar parado para restaurar.
4. Rodar pytest para arquivo, ler tail -n 30; verificar limites e atualizar registros. Sem commit, API externa, instalação ou render.
