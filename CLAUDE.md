# CLAUDE.md — atende-academia

Sistema de atendimento ao aluno para academia/estúdio pequeno: alunos e planos (cobrança só como status manual), aulas coletivas com reserva, lista de espera e falta, check-in e reativação, ficha de treino, explicação animada de exercícios (SVG; MP4 no WhatsApp), avaliação física, conversa (chat web + WhatsApp pela Evolution), equipe pelo Telegram, LGPD e exportação para o Painel do Raio-X de Margem (pacote `servicos`).

- Repo local (sem remoto ainda). Autor de commit: `inematds <inematds@gmail.com>` (config local).
- **Contrato:** `docs/ESPECIFICACAO.md`. Testes caixa-preta em `tests/` (pytest sobe `./atende serve --porta 0`). Contrato e testes são **protegidos** durante a execução longa — só humano altera, e aí recongela o hash (`longrun/.../congelar.sh`).
- Decisões pendentes: `docs/DECISOES-ABERTAS.md`. Relação com o Raio-X: `docs/MAPA-RAIO-X.md`.
- Execução longa: `longrun/2026-10-05-academia-v1/` (método em `~/projetos/execucao-longa`). Como rodar: `README.md`, seção "Como rodar no seu ambiente".
- `python3` (não existe `python` neste host). Sem dependência externa no v1 (biblioteca padrão + SQLite).
- Nenhuma API (WhatsApp/Meta, LLM pago, Pix/PSP, geração de imagem/vídeo, OpenRouter, Groq) sem autorização explícita. Sem rede externa no código. Os 12 SVGs são desenhados à mão; o MP4 é HyperFrames **local** (`tools/render-exercicios`), passo de build fora do pytest e do loop.
- Datas: vigência de matrícula inclusiva nas duas pontas (`fim = inicio + vigencia_dias − 1`); reserva até `hoje + reserva_antecedencia_dias` inclusive; intervalos de aula/avaliação semiabertos `[inicio, fim)`.
- Servidor de teste: só `127.0.0.1`, porta 0; matar só o PID que subiu (nunca `pkill -f`).
- Versão em `VERSION` (semver do CLAUDE global: minor carrega o patch).

## Self-learning

When I correct you, or you catch yourself making a mistake: before continuing, add the lesson as a one-line rule under ## Lessons, so it never happens again.

## Lessons
- Toda contagem de dias/ocupação esperada num teste vem de `python3 -c "import datetime ..."` e fica no comentário do teste; nunca de cabeça.
- SVG animado que vira MP4 pelo HyperFrames: **só CSS `@keyframes`** (o render busca quadro a quadro por `document.getAnimations()` — adaptador `waapi`; o `css` filtra só elementos HTML); **SMIL não tem adaptador** (nada chama `pauseAnimations`/`setCurrentTime`). Conferido em `dist/hyperframe-runtime.js` 0.7.109 e 0.8.86 (05/10/2026). Antes de afirmar o que um render "avança", ler o código do pacote, não só a skill.
- Prova de movimento com Chromium headless: screenshot numa pasta **dentro do repo** (o chromium do snap não grava em `/tmp`); o chrome do Playwright neste host está em `chromium-*/chrome-linux-arm64/chrome` (glob `chrome-linux*`); só `--disable-threaded-animation` faz `transform` seguir `--virtual-time-budget`; calibrar cada candidato com um SVG estático + um CSS animado conhecido antes de julgar os SVGs do repo. Ferramenta ausente (docker, npx, ffprobe) = `PULADO`, nunca traceback nem "ok". (05/10/2026)
