# Estado — ciclo 5

## Funciona
- Base HTTP concorrente, auth, JSON, SQLite/WAL, semente única, alunos/planos/matrículas, aulas/reservas/espera, check-in e tarefas locais preservados.
- Catálogo editável, fichas atômicas e Training.today com rotação por dias de check-in anteriores a hoje; ainda sem conexão com chat.
- Os 12 SVGs de exercícios em web/exercicios: figuras articuladas desenhadas em código, animação CSS de poses/cabeça/equipamento em 2 ou 4 segundos, sem SMIL. Todos os 14 testes estáticos/de arquivos passaram.
- Páginas públicas /exercicios/<id> usam template em web/exercicio.html, passos ordenados, erros e cuidados escapados; exercício sem SVG não inclui .svg no HTML. Rotas SVG/MP4 retornam bytes e MIME corretos, pasta MP4 pelo ambiente e caminhos restritos (incluindo resolução de symlinks).
- Versão 0.5.0. Suíte completa: **43 passed / 56 failed** em 18.91s (pytest-ciclo-5.log). **LIMITES OK**, hash a768b39fe2101c18 e 99 testes preservados.
- Verificação HTTP adicional: HTML sem SVG, escape de conteúdo cadastrado, travessia de diretório recusada e bytes SVG íntegros. Detector de HTML sem achados. Movimento em navegador e render MP4 não executados neste ciclo.

## Falta
- Avaliação física (§8), conflitos/horários/resultados e integração dos lembretes já preparados em Attendance.
- Conversa completa na ordem §11, reutilizando Training.today, Attendance e Classes.
- Reenvio nas tarefas; campanhas, LGPD, Raio-X, demais cadastros/backup, Evolution/Telegram com servidores falsos.
- Docker/.env.exemplo/README Deploy na VPS; escrever tools/render-exercicios sem executar; páginas / e /equipe.
- Não concluído: 56 falhas por funcionalidades pendentes; nenhum conflito teste/spec identificado.

## Como retomar
1. Ler goal → state → plan → canal → fim de progress/failures. Spec completa e conftest relidos neste ciclo.
2. Implementar avaliação física conforme §8; em seguida conversa na ordem exata §11.
3. Resource em src/exercise_pages.py permite respostas binárias/HTML no handler. Template usa string.Template e escape de todo conteúdo do catálogo. file_path restringe SVG/MP4 às pastas reais; reutilizar para verificar mídia no envio futuro.
4. Rodar pytest completo para arquivo com tail -n 30; verificar limites e atualizar registros. Sem commit, rede externa ou execução de render.
