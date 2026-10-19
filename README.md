# atende-academia

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Atende Academia](guia/assets/banner.jpg)](https://inematds.github.io/atende-academia/guia/)

## 📖 Guia de uso

Landing e guia passo a passo (PT/EN/ES): **https://inematds.github.io/atende-academia/guia/** · [English](https://inematds.github.io/atende-academia/guia/en/) · [Español](https://inematds.github.io/atende-academia/guia/es/)

Atendimento ao aluno de uma academia ou estúdio pequeno, em Python 3 só com biblioteca padrão (HTTP + SQLite): alunos e planos, aulas coletivas com reserva e lista de espera, check-in e reativação, ficha de treino, **explicação animada de exercícios**, avaliação física, conversa por chat web e WhatsApp (Evolution API), equipe pelo Telegram, LGPD e exportação para o Painel de Recuperação do Raio-X de Margem.

**Estado (19/10/2026): implementação parcial v0.10.0 — módulos locais, cadastros, backup e Evolution com texto/MP4/reenvio; 84/99 testes passam. Faltam Telegram, páginas e entrega Docker/render.** Ver "Como rodar no seu ambiente".

## O que o sistema faz (v1)

- **Alunos e planos:** cadastro com código de check-in; planos mensal/trimestral/anual/aulas avulsas com preço e vigência; matrícula com status `ativa`, `vencida`, `trancada`, `cancelada`; cobrança só como **status manual** (`pago`/`pendente`) e aviso de vencimento.
- **Aulas coletivas:** grade semanal (modalidade, professor, sala, vagas); reserva com limite de vagas e antecedência; cancelamento com prazo; lista de espera com oferta automática; falta automática (reserva sem check-in); última vaga disputada → um 201, o resto 409.
- **Check-in e frequência:** por código na recepção ou pelo chat ("cheguei"); aluno sem check-in há N dias recebe reativação (só com consentimento); frequência e números do mês para o Raio-X.
- **Treino:** professor monta a ficha com exercícios da biblioteca (séries, repetições, carga, descanso); o aluno pede "meu treino de hoje"; qualquer exercício do catálogo tem **animação SVG** (`/exercicios/<id>`) e, no WhatsApp, MP4 gerado pelo HyperFrames quando existir.
- **Avaliação física** agendada com o professor; resultado é dado sensível (só equipe, nunca pela conversa).
- **Conversa:** aulas, reservar/cancelar, meu plano, meu treino, explicar exercício, FAQ, atendente humano, alerta de saúde (192), "PARAR".
- **Equipe:** página `/equipe` com token e Telegram (`/aulas [data]`, `/fila`, `/responder`, `/encerrar`, avisos de reserva e cancelamento).
- **Campanhas** só com consentimento e trava mínima de publicidade; **LGPD** (exportar, anonimizar); **backup/restauração**; **Docker** para VPS.

Contrato completo: `docs/ESPECIFICACAO.md` (22 seções). Fora do v1: seção 16.

## Como rodar no seu ambiente

O projeto está **planejado, não implementado**: contrato e testes congelados, um agente implementa até os 99 testes passarem. Qualquer pessoa pode rodar no próprio ambiente.

### Pré-requisitos

- Linux/macOS com `git`, `python3` ≥ 3.10 e `pytest` (`pip install pytest`; é ferramenta de desenvolvimento, a aplicação não depende dela).
- Um agente pela **assinatura**: Codex CLI (`codex`) ou Claude Code (`claude`). Nenhuma API é chamada.
- Para a verificação independente final: `docker`; opcionalmente um Chromium (Playwright ou binário) para a prova de movimento dos SVGs e Node 22 + HyperFrames + `ffprobe` para conferir o MP4 — sem eles o verificador imprime `PULADO` para aquela etapa (nunca "ok" silencioso). O verificador e o `tools/render-exercicios` só usam o HyperFrames já instalado (`npx --no-install hyperframes`); para instalar uma vez: `npm install hyperframes` na raiz do repo (`node_modules/`, `package.json` e `package-lock.json` estão no `.gitignore`, então o `verificar-limites.sh` não os vê) ou `npm install -g hyperframes`. Instale **depois** que o loop fechar (antes da verificação independente): o agente não precisa dele e não deve baixar pacote.
- Método e ferramentas de execução longa: clone de `~/projetos/execucao-longa` (`tools/loop-longrun.sh`, `docs/PLANO-EXECUCAO-LONGA.md`). Se não tiver, a rota `/goal` interativa (abaixo) não precisa dele.

### 1. Responder as decisões e congelar o contrato

```sh
cd atende-academia
# leia docs/DECISOES-ABERTAS.md; "ok em tudo" = nada a mudar
python3 -m pytest -q --collect-only | tail -n 1     # 99 tests collected
bash longrun/2026-10-05-academia-v1/congelar.sh     # grava hash-congelado.txt e faz 1 commit
```

Se mudar algo marcado ⚠ nas decisões, edite `docs/ESPECIFICACAO.md` e os testes **antes** de congelar. Depois de congelado, contrato, testes e os dois verificadores são protegidos: o agente não os altera; se um teste contradizer a spec, ele registra em `failures.md` e para (portão humano).

### 2a. Loop headless (Codex `gpt-6-astra`)

```sh
~/projetos/execucao-longa/tools/loop-longrun.sh longrun/2026-10-05-academia-v1
```

Configuração em `longrun/2026-10-05-academia-v1/loop.env` (teste rápido/final, arquivos protegidos, 20 ciclos × 30 min, 8 GB, parada após 3 ciclos sem avanço, `CODEX_ARGS` liberando socket local no sandbox). O loop faz `flock`, `timeout`, `MemoryMax`, reverte ciclo que mexer em arquivo protegido, commita checkpoint por ciclo e para sozinho quando o teste final passa.

### 2b. `/goal` no Codex TUI

```sh
cd atende-academia && codex -c sandbox_workspace_write.network_access=true
```

Cole `longrun/2026-10-05-academia-v1/prompt-goal-codex.md` inteiro (começa com `/goal`). Acompanhe com `/goals`; `/goal pause|resume`.

### 2c. `/goal` no Claude Code

Sessão **nova** do Claude Code aberta na pasta do projeto; siga `longrun/2026-10-05-academia-v1/prompt-goal-claude.md` (condição do `/goal` + o bloco de `prompt-goal-codex.md` como primeira mensagem).

### 3. Acompanhar

```sh
tail -n 20 longrun/2026-10-05-academia-v1/loop.log        # headless
cat longrun/2026-10-05-academia-v1/state.md               # Funciona / Falta / Como retomar
tail -n 5 longrun/2026-10-05-academia-v1/progress.md
python3 -m pytest -q tests/ | tail -n 3
```

Pronto = `python3 -m pytest -q tests/` → **99 passed** e `bash longrun/2026-10-05-academia-v1/verificar-limites.sh` → **LIMITES OK** (hash do contrato intacto, nº de testes igual, só arquivos do escopo, sem dependência externa, sem URL externa no código, sem chave, sem `0.0.0.0` no código, nada de MP4/`node_modules` commitado).

### 4. Verificação independente (nível 4, humano)

```sh
python3 longrun/2026-10-05-academia-v1/verificar-independente.py   # INDEPENDENTE OK
```

Procura valores do fixture copiados no código; sobe uma academia **nunca vista** (outra grade, planos, prazos, feriado, relógio) e confere regras que só passam se a lógica for geral; abre 3 SVGs num Chromium headless e exige que dois quadros em instantes diferentes sejam diferentes (prova de movimento; sem Chromium que passe na calibração → `PULADO`); se o HyperFrames estiver instalado, renderiza um exercício com `tools/render-exercicios` e confere 720×720, ~4 s, sem áudio com `ffprobe` (senão → `PULADO`); faz `docker build` e testa o healthcheck do container (sem `docker` → `PULADO`). A última linha diz `INDEPENDENTE OK (movimento: ..., hyperframes: ..., docker: ...)` para você ver o que foi de fato conferido. Depois abra `/`, `/equipe` e `/exercicios/prancha` no navegador.

## Executar (depois de implementado)

```sh
mkdir -p dados && cp exemplos/academia.json dados/academia.json   # edite nome, token, grade, planos
./atende serve --porta 8080 --dados dados
./atende raiox --dados dados --mes 2026-10 --acompanhamento acompanhamento.json
./atende backup --dados dados --saida backups/academia.zip
```

Chat do aluno em `/`, equipe em `/equipe` (token de `academia.json` no header `X-Token`), animação de cada exercício em `/exercicios/<id>`. `PUBLIC_URL` (endereço público, HTTPS, sem barra final) entra nos links enviados ao aluno; sem ela os links são relativos.

**MP4 dos exercícios (WhatsApp não mostra SVG):** `tools/render-exercicios [--ids a,b] [--saida DIR]` gera `web/exercicios/<id>.mp4` (720×720, 4 s em loop, sem áudio) a partir de cada SVG com o HyperFrames — render local por Chromium, sem API nem conta. Precisa de Node 22+, HyperFrames instalado (`npm install hyperframes` na raiz; o script não baixa nada sozinho) e `ffprobe`. A composição é **só CSS** (o SVG inline dentro de `data-width="720" data-height="720" data-duration="4"`, sem GSAP nem CDN): o render busca cada quadro pelos adaptadores CSS/WAAPI, por isso os SVGs usam `@keyframes` com durações de 1, 2 ou 4 s e nunca SMIL. É um passo de build: roda uma vez na máquina de quem publica, não no servidor nem nos testes. Com o MP4 presente e `PUBLIC_URL` definida, o bot envia o vídeo por `sendMedia`; senão manda o link da página.

## Arquivos

- `docs/ESPECIFICACAO.md` — contrato (22 seções, tabela de rotas, regras com fronteiras, fora do v1).
- `docs/DECISOES-ABERTAS.md` — decisões com proposta padrão; perguntas para o dono.
- `docs/MAPA-RAIO-X.md` — cada vazamento do pacote `servicos` → peça do v1 ou motivo de ficar fora.
- `tests/` — 99 testes caixa-preta (`conftest.py` sobe o CLI, relógio fixo, servidor falso de Evolution/Telegram, pasta temporária de MP4). Fixture em `tests/fixtures/academia.json`; cópia em `exemplos/`.
- `longrun/2026-10-05-academia-v1/` — goal (nível 3+), plan, state, loop.env, prompts, `congelar.sh`, `verificar-limites.sh`, `verificar-independente.py`.
- `FALHAS.md` — uma linha por falha (data, o que quebrou, menor correção, prompt | infra).
