# Estado — concluído (2026-10-19, retomada pelo Claude após o ciclo 11 interrompido)

## Funciona
- Tudo do contrato v1: base HTTP, alunos/planos/matrículas, aulas/reservas/espera/créditos, check-in/tarefas, treino e 12 SVGs CSS, avaliação, conversa, campanhas/LGPD/Raio-X, cadastros, backup, Evolution (texto/MP4/reenvio).
- Telegram §21 em `src/telegram.py`: abertura com `#id` (ALTA quando alerta), repasse das mensagens do aluno em resposta à abertura, resposta em cima, `/responder`, `/encerrar`, `/fila`, `/aulas [data]`, avisos de reserva e cancelamento pelo chat. Webhook com segredo (401) e filtro de chat.
- Páginas `/` (chat) e `/equipe` (grade, reservas, check-in, alunos/matrículas, planos, fichas, biblioteca, fila humana, saída, campanha, Raio-X), sem CDN.
- Entrega: Dockerfile (python:3-slim, sem instalar dependência, HEALTHCHECK python3), docker-compose.yml (127.0.0.1:8080), .env.exemplo vazio, .dockerignore, `tools/render-exercicios` (não executado com HyperFrames: pacote não instalado → código 2 "pulado").
- Versão 0.11.0. `pytest` **99 passed**; **LIMITES OK**; **INDEPENDENTE OK (movimento: chromium, hyperframes: pulado, docker: ok)**.

## Falta (humano)
- Instalar HyperFrames (`npm install hyperframes`) e rodar `tools/render-exercicios` para gerar os MP4 e conferir o passo `hyperframes` do verificador.
- Abrir `/`, `/equipe` e `/exercicios/prancha` no navegador (nível 4).
- Deploy na VPS (README "Deploy na VPS"), push/publicação.
