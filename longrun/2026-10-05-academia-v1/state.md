# Estado — ciclo 8

## Funciona
- Base HTTP concorrente, auth/JSON, SQLite/WAL, semente única; alunos/planos/matrículas, aulas/reservas/espera/créditos, check-in e tarefas locais.
- Catálogo/fichas e treino do dia; 12 SVGs CSS e páginas/arquivos públicos restritos; avaliação física com agenda/conflitos/resultados privados.
- Conversa local persistente (§11), fila humana local, suspensão do bot exceto saúde, histórico por telefone.
- Campanhas com consentimento, opt-out e todas as violações de publicidade devolvidas antes de criar saída.
- LGPD: exportação reúne histórico direto e saída automática/humana; anonimização limpa identificação, textos, ficha, resultados, conversas e fila; cancela reservas/espera/avaliações sem ofertar vaga e preserva agregados.
- Raio-X: indicadores mensais pela API e CLI; mescla valores sobre mês anterior/base, preserva campos não medidos e substitui mês sem duplicar.
- Versão 0.8.0. Suíte: **74 passed / 25 failed** em 54.83s (pytest-ciclo-8.log); foco campanhas/LGPD/Raio-X: **8 passed**. **LIMITES OK**, 99 testes e contrato preservados.
- HTTP adicional confirmou anonimização de saída humana/fila, persistência após reinício, telefone antigo desconhecido, autenticação e validação de campanha.

## Falta
- Cadastros de professores/grade/FAQ/modalidades/salas e backup/restauração.
- Evolution/sendMedia/reenvio e Telegram, incluindo avisos pelo chat e repasse de mensagens humanas; testar exclusivamente contra servidor falso.
- Docker/.env.exemplo/README Deploy na VPS; tools/render-exercicios (escrever, não executar); páginas / e /equipe.
- 25 falhas restantes por módulos ainda ausentes; não concluído. Nenhum conflito teste/spec identificado.

## Como retomar
1. Ler goal → state → plan → canal → fim de progress/failures. Especificação inteira e conftest lidos neste ciclo.
2. Completar cadastros e backup, depois integrações. Privacy e raiox usam a transação do dispatcher; raiox CLI usa a mesma função report da API.
3. Mensagens diretas estão em mensagens; automáticas/humano em saida. A anonimização deixa telefone=None e texto vazio; o futuro reenvio não deve tentar enviar essas mensagens.
4. Rodar pytest para arquivo, ler tail -n 30; verificar limites e atualizar registros. Sem commit, API externa, instalação ou render.
