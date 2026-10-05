# Goal — academia-v1

- **Início:** 2026-10-05 (planejado; execução ainda não iniciada) · **Agente:** `codex exec` (gpt-6-astra, assinatura) em loop headless — `~/projetos/execucao-longa/tools/loop-longrun.sh` · alternativa: `/goal` no Codex TUI ou no Claude Code
- **Tetos:** 20 ciclos × 30 min (≤ 10 h) · memória 8G por ciclo · estagnação 3 ciclos

## Resultado
`./atende` sobe um sistema de atendimento ao aluno para academia/estúdio pequeno — alunos e planos (status manual de pagamento, aviso de vencimento), aulas coletivas com reserva, lista de espera, falta automática e cancelamento pela equipe, check-in e reativação, ficha de treino e "meu treino de hoje", biblioteca com **12 exercícios animados em SVG** (`web/exercicios/`) e página `/exercicios/<id>`, avaliação física, conversa (chat web + WhatsApp pela Evolution, com MP4 por `sendMedia`), equipe pelo Telegram e por `/equipe`, campanhas com trava, LGPD, Raio-X (pacote `servicos`), backup, Docker e a ferramenta de build `tools/render-exercicios` —, conforme `docs/ESPECIFICACAO.md`.

## Especificação
**`docs/ESPECIFICACAO.md`** (contrato completo, congelado). Contexto: `docs/MAPA-RAIO-X.md`, `docs/DECISOES-ABERTAS.md`. Fora do escopo: seção 16 da especificação.

## Critérios de pronto (verificáveis)

**Função**
- [ ] `python3 -m pytest -q tests/` → **99 passed**, 0 failed, 0 errors, 0 skipped (inclui os 14 testes de `test_exercicios_svg.py`: 12 arquivos válidos, animados **só por CSS** com durações 1/2/4 s, sem SMIL/script/URL, ≤ 60 KB; catálogo; rotas `.svg`/`.mp4` — e, em `test_docker.py`, o teste estático de `tools/render-exercicios`)

**Regressão**
- [ ] a mesma suíte inteira no teste final (o loop só fecha se todas passam juntas; teste que passava e voltou a falhar impede o fecho)
- [ ] `./atende serve` reiniciado com o mesmo `--dados` mantém o estado (coberto por `test_estado_persiste_ao_reiniciar`, `test_semente_so_na_primeira_vez`, `test_reativacao_apos_inatividade`, `test_meu_treino_pelo_chat_rotaciona`, `test_cancelar_dentro_e_fora_do_prazo`, `test_presenca_manual_e_automatica`)

**Limite**
- [ ] `bash longrun/2026-10-05-academia-v1/verificar-limites.sh` → `LIMITES OK` (hash do contrato = `hash-congelado.txt` — cobre `tests/`, `pytest.ini`, `docs/ESPECIFICACAO.md`, `verificar-limites.sh` e `verificar-independente.py`; nº de testes coletados = 99; só arquivos do escopo — `atende`, `src/`, `web/`, `tools/`, `exemplos/`, `README.md`, `VERSION`, `Dockerfile`, `docker-compose.yml`, `.env.exemplo`, `.dockerignore`, `.gitignore`, `CLAUDE.md`, `FALHAS.md`, esta pasta —; sem SDK/dependência externa; sem chave de API; sem URL externa no código, em `tools/` nem na entrega (a composição do render é só CSS, sem GSAP/CDN); sem SMIL em `web/exercicios/`; sem `0.0.0.0` no código; nenhum `.mp4` nem `node_modules` commitado)

**Teste rápido por ciclo**: `python3 -m pytest -q tests/`
**Teste completo no final**: `python3 -m pytest -q tests/ && bash longrun/2026-10-05-academia-v1/verificar-limites.sh`

**Depois do "concluído" (humano, nível 4):** `python3 longrun/2026-10-05-academia-v1/verificar-independente.py` → `INDEPENDENTE OK (movimento: ..., hyperframes: ..., docker: ...)` (sem valores do fixture no código + academia nunca vista + prova de que 3 SVGs se mexem num Chromium headless + render de 1 MP4 com HyperFrames conferido por `ffprobe` + `docker build` e healthcheck do container; ferramenta ausente = `PULADO` explícito, nunca "ok" silencioso nem traceback) e abrir `/`, `/equipe` e `/exercicios/prancha` no navegador.

## Restrições
- só pela assinatura; nenhuma API, nenhuma rede externa, nenhuma dependência fora da biblioteca padrão do Python (decisão 2 de `docs/DECISOES-ABERTAS.md`); nenhum gerador de imagem/vídeo: os SVGs são desenhados à mão no código, animados **só por CSS** (`@keyframes`, sem SMIL — seção 7.1)
- não mexer em: `tests/`, `pytest.ini`, `docs/` (inclusive `ESPECIFICACAO.md`), `goal.md`, `hash-congelado.txt`, `congelar.sh`, `verificar-*.{sh,py}`, `loop.env`, `prompt.md` (o hash congelado cobre `tests/`, `pytest.ini`, a spec e os dois verificadores)
- `README.md`: acrescentar "Deploy na VPS" sem remover "Como rodar no seu ambiente" (o teste do README exige as duas)
- `tools/render-exercicios` precisa existir e ser executável (teste estático), mas **não deve ser executado no loop**: `npx hyperframes` baixa pacote (rede) e é lento; é passo de build do humano
- servidor só em `127.0.0.1`; ao testar à mão, porta 0 e matar só o PID que subiu
- no loop headless não fazer commit (o loop faz); no /goal interativo, commit local a cada checkpoint; nunca criar repo remoto nem fazer push

## Portões humanos (parar e perguntar)
- teste que contradiz a especificação (registrar em `failures.md` com o trecho exato e parar — não "ajustar" o teste)
- qualquer chamada a API real (Evolution, Telegram, LLM, Pix, imagem/vídeo) — durante a execução só os servidores falsos locais dos testes; dependência externa; instalar pacote
- deploy na VPS e geração dos MP4 (são do humano, com as credenciais e a máquina dele)
- mudança de contrato, criar repo, push, publicar
