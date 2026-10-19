# Progresso (só acrescentar)

| data/hora | checkpoint | commit | critério atingido? | tokens in/cached/out | compactações |
|---|---|---|---|---|---|
| 2026-10-19 13:50 -0300 | Ciclo 1: base HTTP/SQLite + alunos/planos/matrículas; auth e persistência após reinício verificadas; pytest 9 passed / 90 failed (18.00s); LIMITES OK | sem commit (loop externo) | parcial | — | 0 |

| 2026-10-19 13:54 -0300 | Ciclo 2: aulas/reservas/créditos/cancelamentos/presença manual/espera e saída simulada, v0.2.0; pytest 20 passed / 79 failed (19.58s); LIMITES OK | sem commit (loop externo) | parcial | — | 0 |

| 2026-10-19 13:56 -0300 | Ciclo 3: check-in, presença automática, vencimento e reativação, v0.3.0; pytest 26 passed / 73 failed; LIMITES OK; concorrência e fronteiras verificadas por HTTP | sem commit (loop externo) | parcial | — | 0 |

| 2026-10-19 14:00 -0300 | Ciclo 4: catálogo editável, fichas persistentes e domínio do treino do dia, v0.4.0; pytest 28 passed / 71 failed (20.91s); LIMITES OK; HTTP/reinício/rotação adicionais aprovados | sem commit (loop externo) | parcial | — | 0 |
