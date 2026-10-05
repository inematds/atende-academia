# FALHAS

| data | o que quebrou | menor correção | prompt \| infra |
|---|---|---|---|
| 2026-10-05 | planejamento: `test_reativacao_apos_inatividade` contava `enviadas == 1` em 19/10, mas o aluno `a2` (mensal 20/09 → 19/10) ganharia **também** o aviso de vencimento naquela rodada (janela 14–19/10) → implementação honesta falharia | `a2` passa a trimestral (fim 18/12); conta conferida com `datetime` | prompt |
| 2026-10-05 | planejamento: `destrancar` chamado duas vezes no mesmo teste (a 2ª sobre matrícula já ativa) sem a spec dizer o que acontece | uma chamada só, que confere `status` e `fim` juntos | prompt |
| 2026-10-05 | planejamento: dois testes de conversa exigiam `"nome" not in` resposta (frágil: um nome de professor ou "em nome de" quebraria implementador honesto — lição do reserva-hotel) | cláusulas removidas; o cadastro/reserva já criados provam a regra | prompt |
| 2026-10-05 | `verificar-independente.py`: a prova de movimento pegou `/snap/bin/chromium` do PATH, que não lê `/tmp` (confinamento snap) e devolve PNG vazio → 3 SVGs "parados" | cada candidato (Playwright → binário ms-playwright → PATH) é testado com um SVG estático antes de valer; nenhum funciona → "pulado" | infra |
| 2026-10-05 | `verificar-independente.py`: animação CSS de `transform` roda no compositor e não segue `--virtual-time-budget` (quadro quase aleatório; SMIL seguia) → SVG CSS animado dava "parado" | flag `--disable-threaded-animation` no Chromium (CSS passa a seguir o tempo virtual; estático continua idêntico) | infra |
| 2026-10-05 | `verificar-independente.py`: contas da academia nunca vista erradas (Beto tem matrícula → novos = 3; dois planos vencem 17/11 → 2 avisos na rodada de 14/11) | contas refeitas com `datetime` e anotadas no comentário | prompt |
