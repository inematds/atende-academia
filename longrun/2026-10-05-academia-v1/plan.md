# Plano (reescrever, não acumular)

## Estratégia atual
Planejamento concluído em 05/10/2026 (spec, 99 testes, decisões, Raio-X, travas). Execução ainda não iniciada: aguarda o dono responder `docs/DECISOES-ABERTAS.md` e rodar `congelar.sh`.

Ordem sugerida de implementação (cada passo fecha um grupo de testes): base (`./atende serve` com `PORTA=`, SQLite em `--dados`, semente de `academia.json`, auth, `Content-Type`) → alunos/planos/matrículas (status, pagamento, vencimento) → grade/ocorrências/reservas/cancelamento/espera/créditos/presença → check-in/reativação → biblioteca/ficha/"meu treino" → **12 SVGs** em `web/exercicios/` + `/exercicios/<id>` → avaliação física → conversa (ordem da §11) → `tarefas/rodar` → campanhas → LGPD → raiox (rota + CLI) → cadastros/backup → Evolution (`sendText` + `sendMedia`) → Telegram → Docker/`.env.exemplo`/README ("Deploy na VPS" sem remover "Como rodar") → `tools/render-exercicios` (sem executar) → páginas `/` e `/equipe`.

## Próximos passos
1. Dono: ler `docs/DECISOES-ABERTAS.md`; se mudar ⚠, editar spec + testes; `bash longrun/2026-10-05-academia-v1/congelar.sh`.
2. Iniciar: `~/projetos/execucao-longa/tools/loop-longrun.sh longrun/2026-10-05-academia-v1` (ou `/goal`, ver README).
3. Ao "concluído": `python3 longrun/2026-10-05-academia-v1/verificar-independente.py`, abrir as páginas, gerar os MP4 com `tools/render-exercicios` na máquina de build.
