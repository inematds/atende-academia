# Estado — atualizado 2026-10-05 (planejamento)

## Funciona
- Nada implementado ainda (por desenho: este repo contém só contrato, testes e a pasta de execução longa).
- `python3 -m pytest -q --collect-only` → 99 coletados sem erro; `python3 -m pytest -q` → 0 passed (30 failed, 69 errors: `./atende` não existe).
- Harness conferido com stub temporário (apagado): `./atende` que só imprime `PORTA=<n>` e responde `/api/saude` faz `test_saude_traz_versao_do_arquivo` passar e é derrubado no teardown.
- Travas conferidas em clone temporário: `congelar.sh` grava hash e nº de testes; stub honesto (`EVOLUTION_API_KEY`, `apikey`, `@s.whatsapp.net`, `http://127.0.0.1:8080`, SVG com xmlns do W3C, `tools/render-exercicios` com o CDN do GSAP) → `LIMITES OK`; `https://api.telegram.org` no código → `LIMITE VIOLADO`.

## Falta
- Tudo da seção "Resultado" do `goal.md`: implementação em `atende` + `src/` + `web/` (inclusive os 12 SVGs) + `tools/render-exercicios` + entrega Docker + README "Deploy na VPS".

## Como retomar (comandos exatos)
```
cd ~/projetos/atende-academia
cat longrun/2026-10-05-academia-v1/goal.md          # critérios
python3 -m pytest -q tests/ | tail -n 3             # progresso = nº de passed
bash longrun/2026-10-05-academia-v1/verificar-limites.sh
```

Ao retomar/após compactação: ler goal.md → state.md → plan.md → canal.md → fim de progress.md e failures.md. Na primeira vez, ler `docs/ESPECIFICACAO.md` inteiro e `tests/conftest.py`.
