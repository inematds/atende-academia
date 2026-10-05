/goal
RESULTADO: `./atende` (Python 3, só biblioteca padrão; `src/` + `web/` + `tools/`) implementa docs/ESPECIFICACAO.md por inteiro — atendimento ao aluno de academia/estúdio: alunos, planos e matrículas (status manual de pagamento), aulas coletivas com reserva, espera e falta, check-in e reativação, ficha de treino, 12 exercícios animados em SVG com página própria, avaliação física, conversa (chat web + WhatsApp pela Evolution com MP4 por sendMedia), equipe no Telegram e em /equipe, campanhas, LGPD, Raio-X, backup, Docker e a ferramenta de build tools/render-exercicios.

VERIFICAÇÃO (só termina quando todos passarem, mostrando a saída):
- `python3 -m pytest -q tests/` → 99 passed, 0 failed, 0 errors
- `bash longrun/2026-10-05-academia-v1/verificar-limites.sh` → LIMITES OK

RESTRIÇÕES: não altere tests/, pytest.ini, docs/, goal.md, hash-congelado.txt, congelar.sh, verificar-*, loop.env, prompt.md. Só biblioteca padrão; nenhuma API, rede externa, chave ou pacote instalado; nenhum gerador de imagem (os 12 SVGs são desenhados à mão no código, animados só por CSS @keyframes com durações 1/2/4 s — sem SMIL, seção 7.1); servidor só em 127.0.0.1; matar só o PID que subiu (nunca `pkill -f`). Escreva tools/render-exercicios (composição só CSS, sem GSAP nem CDN; detecta o HyperFrames com `npx --no-install`) mas não o execute (npx baixa pacote; é passo de build do humano). Não commite .mp4 nem node_modules. Uso só pela assinatura. Commit local a cada checkpoint com autor inematds; sem push, sem repo remoto.

ESTADO: use longrun/2026-10-05-academia-v1/ (goal.md, plan.md, state.md, progress.md, failures.md, decisions.md, canal.md).
Após qualquer compactação ou retomada, releia goal.md, state.md, plan.md e canal.md antes de agir. Registre no canal.md (só acrescentar) fatos, aprendizados, glossário e armadilhas assim que surgirem.

CICLO: analisar → escolher a próxima ação útil → executar → testar → observar → corrigir → atualizar state/progress → commit no checkpoint → continuar.
Ordem sugerida: base (serve/PORTA/SQLite/semente/auth) → alunos/planos/matrículas → aulas/reservas/cancelamento/espera/créditos/presença → check-in/reativação → biblioteca/ficha/meu treino → 12 SVGs + /exercicios/<id> → avaliação física → conversa (ordem da seção 11) → tarefas/rodar → campanhas → LGPD → raiox → cadastros/backup → Evolution (sendText + sendMedia) → Telegram → Docker/.env.exemplo/README → tools/render-exercicios → páginas.
Evolution e Telegram: só pelas variáveis de ambiente, testados contra o servidor falso dos testes; nunca chamar API real; nenhuma URL em .env.exemplo.
README: acrescentar a seção "Deploy na VPS" sem remover "Como rodar no seu ambiente".
Enquanto existir uma próxima ação objetiva, segura e alinhada ao objetivo, execute-a sem esperar nova instrução.
3 ciclos sem avanço mensurável (nº de testes passando) = parar, registrar em failures.md e me chamar.
Teste que contradiz a especificação = registrar em failures.md e me chamar; nunca alterar teste ou spec.

PARE E ME CHAME SÓ SE: gasto de crédito/API, ação irreversível ou externa (push, repo remoto, apagar, instalar pacote), dependência externa, credencial ausente, decisão de negócio, conflito real entre teste e especificação.
