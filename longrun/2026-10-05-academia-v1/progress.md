# Progresso (só acrescentar)

| data/hora | checkpoint | commit | critério atingido? | tokens in/cached/out | compactações |
|---|---|---|---|---|---|
| 2026-10-19 13:50 -0300 | Ciclo 1: base HTTP/SQLite + alunos/planos/matrículas; auth e persistência após reinício verificadas; pytest 9 passed / 90 failed (18.00s); LIMITES OK | sem commit (loop externo) | parcial | — | 0 |

| 2026-10-19 13:54 -0300 | Ciclo 2: aulas/reservas/créditos/cancelamentos/presença manual/espera e saída simulada, v0.2.0; pytest 20 passed / 79 failed (19.58s); LIMITES OK | sem commit (loop externo) | parcial | — | 0 |

| 2026-10-19 13:56 -0300 | Ciclo 3: check-in, presença automática, vencimento e reativação, v0.3.0; pytest 26 passed / 73 failed; LIMITES OK; concorrência e fronteiras verificadas por HTTP | sem commit (loop externo) | parcial | — | 0 |

| 2026-10-19 14:00 -0300 | Ciclo 4: catálogo editável, fichas persistentes e domínio do treino do dia, v0.4.0; pytest 28 passed / 71 failed (20.91s); LIMITES OK; HTTP/reinício/rotação adicionais aprovados | sem commit (loop externo) | parcial | — | 0 |

| 2026-10-19 14:04 -0300 | Ciclo 5: 12 SVGs CSS manuais + páginas e rotas SVG/MP4 restritas, v0.5.0; pytest 43 passed / 56 failed (18.91s); LIMITES OK; HTML/escape/caminhos verificados por HTTP | sem commit (loop externo) | parcial | — | 0 |

| 2026-10-19 14:07 -0300 | Ciclo 6: avaliação física, conflitos/agenda/resultados protegidos, v0.6.0; pytest 45 passed / 54 failed (18.85s); LIMITES OK; concorrência/auth/reinício/lembretes verificados por HTTP | sem commit (loop externo) | parcial | — | 0 |

| 2026-10-19 14:11 -0300 | Ciclo 7: conversa persistente e fila humana local, v0.7.0; pytest 63 passed / 36 failed (54.13s); LIMITES OK; HTTP/reinício/suspensão/saúde/encerramento verificados | sem commit (loop externo) | parcial | — | 0 |

| 2026-10-19 14:15 -0300 | Ciclo 8: campanhas, LGPD e Raio-X API/CLI, v0.8.0; pytest 74 passed / 25 failed (54.83s); foco 8 passed; HTTP/reinício/anonimização e LIMITES OK | sem commit (loop externo) | parcial | — | 0 |

| 2026-10-19 14:20 -0300 | Ciclo 9: cadastros restantes e backup/restauração com configuração, v0.9.0; pytest 78 passed / 21 failed (55.22s); foco 6 passed; HTTP/restauração em diretório novo e LIMITES OK | sem commit (loop externo) | parcial | — | 0 |

| 2026-10-19 14:25 -0300 | Ciclo 10: Evolution webhook/sendText/sendMedia/reenvio e proteções LGPD, v0.10.0; pytest 84 passed / 15 failed (64.97s); foco 7 passed; HTTP adicional e LIMITES OK | sem commit (loop externo) | parcial | — | 0 |

| 2026-10-19 (Claude, retomada após ciclo 11 interrompido) | Telegram §21 (src/telegram.py: abertura/repasse/comandos/avisos, webhook com segredo), páginas / e /equipe, Dockerfile/compose/.env.exemplo/.dockerignore, tools/render-exercicios, README "Deploy na VPS", v0.11.0; pytest 99 passed; LIMITES OK; INDEPENDENTE OK (movimento: chromium, hyperframes: pulado, docker: ok) | commit local, sem push | concluído | — | 0 |
