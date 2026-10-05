Você está num ciclo de uma execução longa no repo /home/nmaldaner/projetos/atende-academia.

RESULTADO: `./atende` (Python 3, só biblioteca padrão; código em `src/`, páginas e SVGs em `web/`, ferramenta de build em `tools/`) implementa docs/ESPECIFICACAO.md por inteiro — atendimento ao aluno de academia: alunos/planos/matrículas, aulas coletivas com reserva, espera e falta, check-in e reativação, ficha de treino, 12 exercícios animados em SVG com página própria, avaliação física, conversa (chat web + WhatsApp pela Evolution, MP4 por sendMedia), equipe no Telegram e em /equipe, campanhas, LGPD, Raio-X (pacote servicos), backup, Docker.

ANTES DE AGIR: leia longrun/2026-10-05-academia-v1/goal.md → state.md → plan.md → canal.md → últimas linhas de progress.md e failures.md. Na primeira vez, leia docs/ESPECIFICACAO.md inteiro e tests/conftest.py.

NESTE CICLO: escolha a próxima ação útil (comece pela base: `./atende serve` imprimindo `PORTA=<n>`, SQLite em --dados, semente de academia.json, auth, Content-Type JSON; depois alunos/planos/matrículas → aulas/reservas/cancelamento/espera/créditos/presença → check-in/reativação → biblioteca/ficha/meu treino → os 12 SVGs em web/exercicios/ e /exercicios/<id> → avaliação física → conversa (ordem exata da seção 11) → tarefas/rodar → campanhas → LGPD → raiox → cadastros/backup → Evolution (sendText + sendMedia) → Telegram → Docker/.env.exemplo/README → tools/render-exercicios → páginas / e /equipe), implemente, rode `python3 -m pytest -q tests/` (leva segundos). Leia só o fim da saída (`| tail -n 30`); saída longa vai para arquivo.

SVGs (seção 7.1): figura humana esquemática fazendo o exercício, animação SÓ por CSS (`<style>` com @keyframes + animation ... infinite; toda duração 1s, 2s ou 4s), SEM SMIL (`<animate`, `<animateTransform`, `<set`: o render do HyperFrames não avança SMIL), `viewBox`, `<title>` em português, sem `<script>`, `<image>`, `<foreignObject>`, `@import`, sem http fora do xmlns, href/url só com `#`, ≤ 60 KB. Desenhe à mão no código; nenhum gerador de imagem.

tools/render-exercicios (seção 7.4): escreva o script (Python 3 + subprocess; detecta com `npx --no-install hyperframes --version` e sai com código 2 e "pulado: hyperframes não instalado" se faltar; composição SÓ CSS — sem GSAP, sem <script>, sem CDN — com data-width/data-height 720 e data-duration 4 e o SVG inline; `npx hyperframes render <pasta> --output <id>.mp4 --fps 30`; conferência por ffprobe), mas NÃO o execute: `npx hyperframes` baixa pacote e é lento — é passo de build do humano.

AO TERMINAR O CICLO (obrigatório):
- reescreva state.md (Funciona / Falta / Como retomar) e plan.md (próximos 3 passos);
- acrescente 1 linha em progress.md: data-hora, o que mudou, resultado do pytest (N passed / N failed);
- se algo deu errado, 1 linha em failures.md: erro → tentativa → resultado;
- decisões de design em decisions.md; fatos e armadilhas novos em canal.md (só acrescentar);
- quando `python3 -m pytest -q tests/` passar inteiro E `bash longrun/2026-10-05-academia-v1/verificar-limites.sh` imprimir LIMITES OK, escreva "concluído" na primeira linha de "## Funciona" do state.md.

SE UM TESTE CONTRADIZ A ESPECIFICAÇÃO: não altere o teste nem a spec. Registre em failures.md (teste, trecho da spec, o conflito) e siga com os outros itens; isso é portão humano.

INTEGRAÇÕES: Evolution e Telegram só pelas variáveis de ambiente da spec; teste só contra o servidor falso dos testes. Nunca chame api.telegram.org nem uma Evolution real; nunca escreva URL externa no código nem em .env.exemplo (nem em comentário). PUBLIC_URL e EXERCICIOS_MP4_DIR vêm do ambiente.

README: acrescente a seção "Deploy na VPS" (seção 22 da spec) SEM remover a seção "Como rodar no seu ambiente" nem a descrição do projeto; só atualize a linha de estado.

RESTRIÇÕES: não altere tests/, pytest.ini, docs/, goal.md, hash-congelado.txt, congelar.sh, verificar-*, loop.env, prompt.md. Só biblioteca padrão do Python 3 (`python3`, não `python`). Nenhuma API, nenhuma rede externa, nenhuma chave, nenhum pacote instalado. Servidor só em 127.0.0.1. Não commite .mp4 nem node_modules. Não use `pkill -f`; mate só o PID que você subiu. Não faça commit (o loop externo faz).
