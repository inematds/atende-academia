# Validação adversarial do plano — atende-academia (05/10/2026)

Validador independente do planejador (briefing `BRIEF-VALIDACAO.md` + adendo `BRIEF-SAUDE-MOVIMENTO.md`). Nada implementado, nada
enviado, nenhuma API chamada, `congelar.sh` rodado só em clone temporário. Commits: `794f5f6` (correções) e o seguinte (este arquivo).

**Problemas achados: 9** — bloqueia a execução: 2 · atrapalha: 4 · cosmético: 3. Todos corrigidos nos arquivos do projeto;
o que é decisão do dono está na última seção. Contagem de testes: **99 → 99** (um teste mudou de conteúdo, nenhum foi
criado ou removido).

| Gravidade | Problema | Correção |
|---|---|---|
| bloqueia | §7.1 aceitava **SMIL** nos SVGs, mas o render do HyperFrames **não tem adaptador SMIL** (ver seção 0): o MP4 do WhatsApp sairia com a figura parada ou fora de fase, e a fisio já proibia — planos irmãos incoerentes | §7.1 só CSS (`@keyframes`, durações 1/2/4 s, `infinite`), §7.4 composição só CSS sem GSAP/CDN, `test_svg_do_exercicio` espelha a fisio, `verificar-limites.sh` sem exceção do GSAP + grep de SMIL em `web/exercicios/`, goal/prompts/DECISÕES/README |
| bloqueia | §6.3 não dizia a ordem entre "sem ficha" e "sem matrícula": `test_meu_treino_sem_ficha_ou_sem_plano` espera `plano`/`recepção` para quem não tem nenhum dos dois; um implementador que olhasse a ficha primeiro falharia honestamente | §6.3: matrícula ativa primeiro, depois ficha |
| atrapalha | `test_exercicio_novo_sem_svg` exige `".svg" not in html` e `test_rotas_svg_e_mp4` exige `/exercicios/../atende` → 400/404; a §7.2 não dizia nenhum dos dois (um favicon `.svg` na página quebraria) | §7.2 com os dois literais |
| atrapalha | `verificar-independente.py` dava **falha falsa ou traceback** nesta máquina: glob `chromium-*/chrome-linux/chrome` não casa `chrome-linux-arm64`; screenshot em `/tmp` com o chromium do snap = PNG vazio; `docker`/`npx` ausentes ou `subir()` falhando = traceback | candidatos **calibrados** (SVG estático + SVG CSS animado conhecido) numa pasta dentro do repo (`.verif-svg-*`, no `.gitignore`), glob `chrome-linux*`, guardas `shutil.which` + `try` → `PULADO:` explícito; última linha `INDEPENDENTE OK (movimento, hyperframes, docker)` |
| atrapalha | `verificar-limites.sh` liberava `cdn.jsdelivr.net/npm/gsap` em `tools/` (e nada mais — a regex era exata); com a composição só CSS a exceção virou brecha sem função | exceção removida; `tools/` entra no mesmo grep de URL externa do código |
| atrapalha | `tools/render-exercicios` "sai com código 2 sem HyperFrames" mas `npx hyperframes` baixa o pacote sozinho — o script não tinha como saber que "não está instalado" | §7.4: detecta com `npx --no-install hyperframes --version`, nunca baixa; README diz como instalar (`npm install hyperframes`, `node_modules/` ignorado) |
| cosmético | `trancar` de matrícula já trancada / `destrancar` de não trancada sem regra | §3.3 → 409 |
| cosmético | `goal.md` dizia "14 testes de SVG ... e o teste estático de `tools/render-exercicios`" — o estático está em `test_docker.py` | texto corrigido |
| cosmético | README não dizia que o verificador só usa HyperFrames já instalado (`--no-install` sempre daria "pulado") nem que `docker` ausente é `PULADO` | README "Pré-requisitos" e "Verificação independente" |

## 0. Ponto crítico — SMIL × CSS no render do HyperFrames (quem está certo: a fisio, na conclusão)

**Conclusão: SMIL não sai no MP4; só animação CSS/WAAPI é avançada. A spec da academia passou a "só CSS", igual à fisio.**

Fontes (arquivo e trecho):

1. `~/.claude/skills/hyperframes-core/references/determinism-rules.md`, 1º parágrafo: *"HyperFrames seeks compositions
   frame-by-frame. Every frame must be reproducible from its time value alone — same input time → same pixels."*
   `~/.claude/skills/hyperframes/references/frame-worker-core.md` l.73: *"(the renderer seeks frame-by-frame)"*.
2. `~/.claude/skills/hyperframes-animation/adapters/css-animations.md` l.8 e l.20: *"HyperFrames can seek CSS keyframe
   animations through its `css` runtime adapter"*; *"The adapter discovers elements with computed `animation-name`, seeks their
   browser `Animation` handles when available, and falls back to pausing with negative `animation-delay`"*. l.106/115: com
   `animation-iteration-count: infinite` o root **precisa** de `data-duration` (`lint`: `root_composition_missing_duration_source`)
   — a §7.4 põe `data-duration="4"`.
3. `~/.claude/skills/hyperframes-animation/adapters/waapi.md` l.18: *"The adapter calls `document.getAnimations()`, sets each
   animation's `currentTime` to HyperFrames time in milliseconds, then pauses it."*
4. **Código do pacote** (não só a skill), nas duas versões presentes na máquina:
   - 0.7.109 — `~/projetos/hyperframes-student-kit/node_modules/hyperframes/dist/hyperframe-runtime.js`:
     adaptador `css`: `return{name:"css",discover:()=>{...for(let c of u){if(!(c instanceof HTMLElement))continue;let
     m=window.getComputedStyle(c);!m.animationName||...` → **só elementos HTML** (um `<g>` de SVG é `SVGGElement`, fica fora);
     adaptador `waapi` (`function Es()`): `s=()=>{...return document.getAnimations()}` … `seek:y=>{...R.currentTime=F ... R.pause()}`
     → alcança **toda** `Animation` do documento, inclusive as `CSSAnimation` de elementos SVG inline.
   - 0.8.86 — `~/.npm/_npx/702923228c2ce1e6/node_modules/hyperframes/dist/hyperframe-runtime.js`: o filtro do `css` virou
     `ye(e){return Ne(e)&&e.namespaceURI===od}` (namespace XHTML, mesmo efeito); registro incondicional
     `e.deterministicAdapters=[tf(),ud({...}),cd(),...]` (`tf` = waapi, `ud` = css).
   - Ocorrências de `pauseAnimations`, `unpauseAnimations`, `SVGSVGElement`, `setCurrentTime(` de SVG, `SMIL`, `<animate` no
     runtime e no `cli.js`: **nenhuma**, nas duas versões.
5. **Como o render captura** (`dist/cli.js` 0.7.109, l.114579–115048, 150344, 150482, 65241, 69314): instala o shim
   `__HF_VIRTUAL_TIME__` (substitui `Date`, `performance.now`, `requestAnimationFrame`, `setTimeout/Interval`); a cada quadro
   chama `__HF_VIRTUAL_TIME__.seekToTime(ms)` + `window.__hfSeekAllAdapters(t)` e captura por
   `HeadlessExperimental.beginFrame({frameTimeTicks: base + frameIndex × interval, interval, screenshot})` (Linux, headless-shell)
   ou `Page.captureScreenshot` (*"falling back to screenshot mode"*). Não há `setVirtualTimePolicy`. Logo o relógio SMIL do
   documento **não é pausado nem buscado**: em modo `beginframe` avança por coincidência com o relógio do compositor; em modo
   `screenshot` corre em tempo real → quadros fora de fase. Não é contrato: viola a regra 1.

**Sobre a fisio:** veredito certo ("sem SMIL, só CSS"), justificativa imprecisa — `docs/ESPECIFICACAO.md` §25 e DECISÕES 11 dizem
que *"a animação CSS do SVG é avançada pelo adaptador `css`"*; o `css` filtra elementos HTML, quem alcança os elementos do SVG
inline é o **`waapi`** via `document.getAnimations()`. O resultado é o mesmo (só CSS funciona), mas vale corrigir a frase lá
(não editei a fisio).

**GSAP por CDN em `tools/render-exercicios`:** seria aceitável como passo de build fora do loop (o `npx` já precisa de rede), mas
é desnecessário — a composição só CSS não tem `<script>` nenhum. A exceção foi removida: trava mais apertada e idêntica à fisio.
Antes, o `verificar-limites.sh` liberava exatamente `https?://cdn.jsdelivr.net/npm/gsap…` e nada mais (regex); hoje `tools/` entra
no grep geral (prova na seção 6: CDN em `tools/` → `LIMITE VIOLADO`).

**Medição nesta máquina (spark-922b, arm64), SVG CSS animado de 2 s, instantes 250/1150/2450 ms, flag `--disable-threaded-animation`:**
chromium do snap com PNG em `/tmp` → `VAZIO`; com PNG em pasta dentro do repo → 3 hashes distintos; `chrome` do Playwright
(`chromium-1243/chrome-linux-arm64/chrome`) → 3 distintos; `chrome-headless-shell` → 3 distintos (a fisio mediu quadros iguais
**sem** a flag). O verificador segue usando só o chrome completo, como a fisio.

## 1. Teste × especificação, item a item

- **Corrigido**: §6.3 (ordem), §7.2 (`.svg` ausente; `..` → 404/400), §3.3 (409 em trancar/destrancar repetidos), §7.1/§7.4
  (só CSS; durações; detecção do HyperFrames).
- **OK** (conferido teste a teste, 13 arquivos): ordem de listagem definida em todas as rotas (`aulas` por `inicio`+`aula_id`;
  `reservas` por `inicio`+`id`; `espera`, `alunos`, `matriculas`, `fila` por `id`; `checkins` por `quando`+`id`; `avaliacoes` por
  `inicio`+`id`; `planos`/`modalidades`/`exercicios` ordem de cadastro); arredondamento 1 casa e tolerância ±0,06 (§14);
  pontas inclusivas/exclusivas escritas (`fim = inicio + vig − 1`; `hoje + 7` vale; cancelar `agora + 2 h ≤ inicio`; lembrete
  `inicio ≤ agora + 24 h`; reativação `≥ 14`; falta `fim ≤ agora`; intervalos semiabertos na avaliação); desempates (matrícula
  ativa: maior `fim`, depois maior `id`; FAQ: maior %, depois primeiro; exercício: casamento mais longo, depois primeiro);
  códigos 400/401/404/409/422 e a ordem das verificações da reserva (§4.2) e do 401 antes do corpo (§9); formatos literais
  exigidos pelos testes todos escritos (`N) DD/MM HH:MM <modalidade> com <professor>`, `DD/MM HH:MM <modalidade> com <professor> — <livres> vagas`,
  `- <exercício>: SxR, <carga>, descanso N s`, `Treino <nome>`, `1. passo`, `Cuidado: …`, `Veja a animação: <link>`,
  `HH:MM <modalidade> (<professor>) — r/v`, `Nova reserva: DD/MM HH:MM <nome> — <modalidade>`, `Cancelada:`,
  `Por enquanto só consigo ler mensagens de texto.`); contagem exata de mensagens só onde a spec limita (uma por matrícula,
  por avaliação, por período de inatividade; FAQ = só a resposta).
- **Conversa (16 regras)**: sem colisão nos casos testados — `cancelar`/`desmarcar` (9) antes de `marcar` (10); "cancelar" dentro
  do fluxo de reserva é consumido pela regra 4 (sai com `ok`); número puro: fluxo (4) → pendência de espera (5) → senão cai em 16;
  alerta de saúde (1) vence tudo, inclusive atendimento aberto; `avaliacao` (8) antes de `marcar` (10) ("quero marcar minha
  avaliação" → recepção); FAQ (15) só depois de exercício (14). Riscos de substring fora dos testes estão em "Para o dono".

## 2. Contas conferidas (python3, independentes do planejador)

| Conta | Resultado | Onde |
|---|---|---|
| Dias da semana: 05/10 seg, 06/10 **ter**, 07/10 qua, 08/10 qui, 09/10 sex, 11/10 dom, 12/10 seg (feriado), 13/10 ter, 19/10 seg, 20/10 ter | ✓ | todos os testes |
| mensal 06/10 + 29 = **04/11**; anual 06/10/26 + 364 = **05/10/27**; mensal 01/08 + 29 = **30/08**; 10/09 + 29 = **09/10**; aviso 09/10 − 5 = **04/10**; avulso5 06/10 + 59 = **04/12**; 12/09 + 29 = **11/10**; 10/10 + 29 = **08/11**; 01/10 + 29 = **30/10**; trimestral 01/09 + 89 = **29/11**; 20/09 + 89 = **18/12** | ✓ | alunos_planos, aulas, treino, lgpd |
| Reativação: 06/10 − 22/09 = **14** (conta), 06/10 − 20/09 = 16, 06/10 − 23/09 = **13** (não), 19/10 − 23/09 = 26, 19/10 − 06/10 = 13, 20/10 − 06/10 = **14** | ✓ | test_reativacao_apos_inatividade |
| Antecedência: hoje + 7 = **13/10** (vale); 20/10 = hoje + 14 (não) | ✓ | test_reserva_invalida |
| Cancelamento: 07/10 07:00 + 2 h = **09:00 ≤ 09:00** (dentro); 07:30 + 2 h = 09:30 (tarde) | ✓ | test_cancelar_dentro_e_fora_do_prazo |
| Lembrete: 06/10 09:59 + 24 h = 07/10 09:59 < 10:00 (não); 10:00 + 24 h = 07/10 10:00 (inclusive) | ✓ | test_lembrete_avaliacao_uma_vez |
| Vagas out/2026 = seg 4×3 + ter 3×4 + qua (2+2)×4 + sex 4×5 = **60**; 4/60 = 6,67 → 6,7 (|Δ| 0,033 ≤ 0,06); falta 1/3 = **33,3**; recorrente 2/6 = 0,33 → 0,3 | ✓ | test_raiox_numeros_do_mes |
| Retorno: fim 09/10 → janela 09/09..08/11, renovação 10/10 dentro → 1 de 2 = **50,0** | ✓ | idem |
| Avaliação Carla qua (09–12, passo 30, dur 30, pilates 09–10): **10:00 10:30 11:00 11:30**; ter 06/10 09:00 + 2 h: **11:00 11:30**; qui: 6; Eva qua 14–16: **14:00…15:30** | ✓ | test_avaliacao, test_cadastros |
| Treino: k = (check-ins em dias anteriores) mod 2 → **0, 0, 1, 0** (A, A, B, A) | ✓ | test_meu_treino_pelo_chat_rotaciona |
| MP4 falso: 12 + 64 = **76 bytes** | ✓ | test_exercicio_com_mp4 |
| Verificador (nov/2026): 03/11 ter, 19/11 qui (feriado); quinzenal 03/11 + 14 = **17/11**; pacote3 + 44 = **17/12**; 13/11 − 03/11 = **10**; 17/11 − 3 = **14/11**; vagas nov = ter 1×4 + qui 2×3 = **10** → 3/10 = 30,0; falta 2/3 = 66,7; Lia 07:00–21:00 passo 20 dur 40 menos yoga 18–19: 41 − 4 (17:40, 18:00, 18:20, 18:40) = **37**, 07:00…20:20, 17:20 e 19:00 dentro | ✓ | verificar-independente.py |
| `INSTANTES_MS` (250, 1150, 2450): fases distintas para períodos de 1, 2 e 4 s | ✓ | prova de movimento |

## 3. Contradições internas — OK

Nenhum par de testes incompatível; nenhum teste depende de estado de outro (cada um sobe o próprio `--dados`); o fixture
comporta todos os cenários (turnos, 2 vagas no pilates para lotar/concorrer, 4 ocorrências na janela de 7 dias — "5)" não
aparece —, Carla com janela que cruza a aula de pilates, `avulso5` para créditos, feriado numa segunda com aula).

## 4. Burlável? — OK (com uma ressalva humana)

`verificar-independente.py` usa uma academia nunca vista (nome, token, planos de 15/45 dias, pacote de 3 aulas, passo 20,
antecedência 3 dias, cancelamento 24 h, inatividade 10, aviso 3, feriado 19/11, relógio em novembro) com tudo explícito (nenhum
atalho do conftest) e procura literais do fixture no código. O hash cobre `tests/`, `pytest.ini`, a spec e os dois verificadores;
arquivo fora do escopo = violação; `conftest.py`/`pytest.ini` protegidos. Ressalva: um SVG "bolinha que pulsa" passa no pytest e
no nível 4 (quadros diferem); só o humano abrindo `/exercicios/<id>` julga a figura — já previsto na decisão 11 e no goal.

## 5. Raio-X — OK

`valores` só com ids de `~/projetos/raio-x-margem/setores/servicos.js` (`atendimentos_mes`, `falta_pct`, `ocupacao_pct`,
`clientes_novos_mes`, `retorno_atual_pct`, `atendimentos_mes_recorrente` — todos existem em `entradas`); cada mapeamento é
premissa declarada em `docs/MAPA-RAIO-X.md` e na decisão 13; formato do acompanhamento bate com `app/painel-motor.js` l.5–6
(`{tipo:'acompanhamento', pacote, cliente, base:{data, valores}, meses:[{mes, valores, obs}]}`).

## 6. Travas — OK (saída real, clone temporário em `~/.cache`, apagado no fim)

`loop.env`: `CODEX_ARGS="-c sandbox_workspace_write.network_access=true"`, `PERMITIDOS="."`, `PROTEGIDOS` com `tests/
pytest.ini docs/` + goal/hash/congelar/verificar-*/loop.env/prompt.md; prompts proíbem API real e os protegidos; 99 = 99.

```
## 1 congelar.sh no clone
congelado: HASH=a49f6cc245e3ac4d TESTES=99
## 2 stub honesto (EVOLUTION_API_KEY, apikey, @s.whatsapp.net, 127.0.0.1, SVG CSS com xmlns, tools/ sem CDN)
LIMITES OK (hash a49f6cc245e3ac4d, 99 testes, escopo ok, sem API/rede)   rc=0
## 3 https://api.telegram.org no código
src/x.py:6:T = "https://api.telegram.org/bot"
LIMITE VIOLADO: chave/credencial ou API externa no código, nas ferramentas ou na entrega   rc=1
## 4 CDN do GSAP em tools/ (trava apertada)
tools/render-exercicios:3:# <script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js">
LIMITE VIOLADO: URL externa no código, nas ferramentas ou na entrega   rc=1
## 5 SMIL em web/exercicios
LIMITE VIOLADO: SMIL em web/exercicios (seção 7.1: animação só por CSS)   rc=1
## 6 teste alterado
LIMITE VIOLADO: hash do contrato mudou (c240c7b8b6fd6768 ≠ a49f6cc245e3ac4d)   rc=1
## 7 tudo revertido
LIMITES OK (hash a49f6cc245e3ac4d, 99 testes, escopo ok, sem API/rede)   rc=0
## 8 teste de SVG: CSS passa / SMIL falha / duração 1.5s falha
1 passed · 1 failed (tests/test_exercicios_svg.py:31 AssertionError: <animate) · 1 failed (:35 duração fora de 1/2/4 s)
```

## 7. Harness — OK (saída real)

```
python3 -m pytest -q --collect-only | tail -1   → 99 tests collected
python3 -m pytest -q | tail -1                  → 30 failed, 69 errors (0 passed: ./atende não existe)
## 9 stub ./atende (PORTA=<n> + /api/saude) → tests/test_basico.py::test_saude_traz_versao_do_arquivo
1 passed in 0.06s · processos 'atende serve' do clone vivos: 0
## 12 verificar-independente.py ponta a ponta com o stub
rc=1 · tracebacks: 0
MOVIMENTO: chromium — 2/3 SVGs com quadros diferentes        (o 3º era um SVG estático de propósito)
PULADO: hyperframes (pacote não instalado: `npx --no-install hyperframes --version` falhou; `npm install hyperframes` na raiz)
DOCKER: pulado
INDEPENDENTE FALHOU:
 - erro ao conferir a academia nunca vista: AttributeError("'str' object has no attribute 'get'")   (stub responde 404 sem JSON)
 - SVG não se mexe (quadros iguais em (250, 1150, 2450) ms, via chromium): agachamento.svg
 - docker build falhou: ERROR: failed to build: failed to solve: the Dockerfile cannot be empty
processos do clone vivos no fim: 0 · pastas .verif-svg- sobrando: 0
```
O `Externo` falso grava cada pedido e injeta 500 por `externo.falhas` (usado em `test_saida_pela_evolution_com_reenvio`).

## 8. Tamanho e fechamento — OK

"Fora do v1" claro (§16). Nenhum teste exige rede real, Docker real (checagem estática) nem relógio real (`ATENDE_AGORA`);
integrações contra o `Externo` local. Dois testes assíncronos usam `sleep` de 0,5–0,8 s depois de esperar por conteúdo
(aceitável). 99 testes + 12 SVGs desenhados à mão cabem em 20 ciclos × 30 min (o atende-clinica fechou 93 em 7).

## 9. README "Como rodar no seu ambiente" — OK (corrigido)

Caminhos citados existem (`~/projetos/execucao-longa/tools/loop-longrun.sh`, `docs/PLANO-EXECUCAO-LONGA.md`, os três prompts,
`congelar.sh`). Três rotas (loop headless, `/goal` Codex com `network_access`, `/goal` Claude) descritas. Acrescentado: como
instalar o HyperFrames para o verificador e o `tools/render-exercicios` (só `--no-install`), e que `docker`/Chromium/HyperFrames
ausentes viram `PULADO`.

## 10. Vazamento de processo — OK (saída real)

`conftest.py` já tinha `SERVIDORES` + fixture `autouse` que para tudo no teardown. Prova com teste temporário (apagado) que sobe
`Servidor(dados).subir()` fora de `try/finally` e falha de propósito:
```
tests/test_tmp_vaza.py → 1 failed in 0.08s
processos 'atende serve' do clone depois do pytest: 0
```
No fim da validação `pgrep -af "[a]tende serve"` não encontra nenhum processo meu (o clone foi apagado; processos de outras
sessões que apareceram de passagem durante a validação não foram tocados).

## Para o dono decidir (não corrigido de propósito)

- **Fisio**: corrigir a justificativa "adaptador `css`" → "adaptador `waapi` (`document.getAnimations()`)" em §25/decisão 11; o
  veredito (só CSS) fica.
- **Substrings na conversa (§11)**: "contém" é substring — um aluno chamado *Paula* escrevendo "aqui é a Paula, tem estacionamento?"
  cai na regra 11 (`aula`); apelidos `passada` (afundo), `ponte` (elevação pélvica) e `avanco` casam frases comuns ("semana passada").
  Trocar para casamento por palavra inteira é mudança de contrato: decidir antes de congelar.
- `test_resultado_dados_sensiveis_e_chat` exige `"80" not in r and "18" not in r` na resposta "fale com a recepção": uma resposta
  com horário ("das 8h às 18h") quebraria. Baixo risco; mantido.
- **MP4 no WhatsApp**: o v1 precisa de `PUBLIC_URL` com HTTPS e dos MP4 gerados na máquina de build (Node + HyperFrames instalado);
  sem isso o aluno recebe o link da página — pergunta já aberta em DECISÕES.
- **CREF/CONFEF** (decisão 5) e **crédito por reserva × por check-in** (pergunta aberta): a spec decide sem ambiguidade
  (desconta na reserva, devolve só em `cancelada`/`cancelada_pela_academia`; check-in não consome), mas é política do dono.
- Qualidade da figura nos 12 SVGs: só o humano abrindo `/exercicios/<id>` (decisão 11).

## Contagem final

- Testes: **99** coletados (`python3 -m pytest -q --collect-only`), 0 passed sem implementação.
- Arquivos alterados: `docs/ESPECIFICACAO.md`, `docs/DECISOES-ABERTAS.md`, `tests/test_exercicios_svg.py`,
  `longrun/2026-10-05-academia-v1/{goal.md,prompt.md,prompt-goal-codex.md,verificar-limites.sh,verificar-independente.py,state.md}`,
  `README.md`, `CLAUDE.md`, `FALHAS.md`, `.gitignore`, este arquivo.
