# Estado — ciclo 10

## Funciona
- Base HTTP concorrente, auth/JSON, SQLite/WAL, semente única; alunos/planos/matrículas, aulas/reservas/espera/créditos, check-in e tarefas.
- Catálogo/fichas/treino do dia; 12 SVGs CSS e páginas de exercício; avaliação física e resultados privados.
- Conversa persistente (§11), fila humana local e suspensão do bot exceto saúde; campanhas, LGPD e Raio-X API/CLI.
- Cadastros (§18), backup SQLite online em ZIP e restauração da configuração/estado.
- Evolution (§20): segredo próprio antes do corpo, deduplicação persistente, filtros, mensagem estendida, resposta a mídia não textual; sendText e sendMedia de exercício com MP4/PUBLIC_URL, fallback textual. Saída automática e humana tenta envio antes da resposta HTTP; tarefas reenviam pendentes primeiro, respeitando opt-out/anonimização.
- Versão 0.10.0. Suíte completa: **84 passed / 15 failed** em 64.97s (pytest-ciclo-10.log); foco Evolution: **7 passed / 9 deselected**. **LIMITES OK**, contrato e 99 testes preservados.
- HTTP adicional verificou extendedTextMessage, deduplicação após reinício e bloqueio de reenvio após opt-out e anonimização. Somente servidor falso local usado.

## Falta
- Telegram (§21): abertura/repasse da fila humana, respostas/comandos e avisos de reserva/cancelamento pelo chat. Nove falhas da suíte dependem disso, inclusive teste de reserva via WhatsApp.
- Docker/.env.exemplo/README Deploy na VPS; tools/render-exercicios (escrever, não executar); páginas / e /equipe (seis falhas de entrega).
- Não concluído. Nenhum conflito teste/spec identificado. Render, navegador nível 4 e deploy continuam passos humanos.

## Como retomar
1. Ler goal → state → plan → canal → fim de progress/failures. Spec inteira e conftest lidos neste ciclo.
2. Implementar Telegram, reutilizando Conversation.human/change_human/decide e Classes.occurrences. Os webhooks usam segredos próprios, não X-Token. Evolution fica em src/evolution.py; import de Conversation é local para evitar ciclo.
3. O envio atual é síncrono, com timeout de 3 s e sem redirecionamento. Idempotência do webhook fica na coleção evolution_recebidas; respostas diretas ficam em mensagens, automáticas/humano em saida. retry ignora telefone/texto apagados e opt-out de automáticas.
4. Rodar pytest para arquivo, ler tail -n 30; verificar limites e atualizar registros. Sem commit, rede externa, instalação ou render.
