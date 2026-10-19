# Estado — ciclo 4

## Funciona
- Base HTTP concorrente, auth, JSON, SQLite/WAL, semente única, alunos/planos/matrículas, aulas/reservas/espera, check-in e tarefas locais preservados.
- Catálogo de exercícios: lista pública dos ativos, consulta inclusive inativos, criação/edição/desativação com validação; svg calculado pela existência real do arquivo (ainda false, SVGs pendentes).
- Fichas: PUT/GET/DELETE autenticados, substituição atômica, validação dos itens e exercícios ativos; desativação preserva fichas existentes. DELETE responde 204 sem corpo.
- Training.today seleciona treino pelos dias de check-in anteriores a hoje e formata séries, repetições, carga e descanso; verifica plano antes da ficha. Ainda não conectado ao chat.
- Versão 0.4.0. Suíte completa: **28 passed / 71 failed** (pytest-ciclo-4.log). **LIMITES OK**, hash a768b39fe2101c18 e 99 testes preservados.
- Verificação adicional HTTP/domínio aprovada: auth, validação atômica, persistência após reinício, exercício inativo em ficha existente, rotação A/B e ordem plano/ficha.

## Falta
- Os 12 SVGs manuais CSS e páginas/rotas públicas de exercícios; biblioteca só passará seu teste completo quando os arquivos existirem.
- Avaliação física e seus lembretes integrados; conversa completa na ordem §11, incluindo treino, explicação e fluxos de reserva/cancelamento.
- Reenvio pendente nas tarefas; campanhas, LGPD, Raio-X, demais cadastros/backup, Evolution/Telegram com servidores falsos.
- Docker/.env.exemplo/README Deploy na VPS, tools/render-exercicios (escrever sem executar), páginas / e /equipe.
- Não concluído: 71 falhas por funcionalidades pendentes; nenhum conflito teste/spec identificado.

## Como retomar
1. Ler goal → state → plan → canal → fim de progress/failures. Spec completa e conftest lidos no ciclo 4.
2. Começar pelos 12 SVGs CSS em web/exercicios e suas rotas/páginas (§7); depois avaliação (§8), então conversa na ordem exata §11.
3. Usar Training(app).catalog/exercise/edit_exercise/ficha/today; Store.delete agora remove entidades dentro da transação. Não duplicar seleção/formatação do treino no chat.
4. Rodar pytest completo para arquivo com tail -n 30; verificar limites e atualizar registros. Sem commit, rede externa ou execução do render.
