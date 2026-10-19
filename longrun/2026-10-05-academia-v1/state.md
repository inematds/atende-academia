# Estado — atualizado 2026-10-19, ciclo 1

## Funciona
- Base executável `./atende serve --porta 0 --dados DIR`: ThreadingHTTPServer, bind padrão em 127.0.0.1, primeira linha PORTA=<n>, saúde com VERSION e JSON UTF-8.
- Diretório de dados criado automaticamente; academia.json copiado do exemplo se ausente. SQLite com WAL, semente dos sete catálogos somente uma vez e transações protegidas por RLock.
- Autenticação X-Token antes de ler/validar o corpo; classificação das rotas públicas segundo §9. Rotas ainda não implementadas retornam 404 (não há respostas simulando implementação).
- Alunos: criação, telefone normalizado/deduplicado, código único, busca sem acento, edição e conflito de telefone.
- Planos: listagem pública, criação, edição e desativação. Matrículas: vigência inclusiva, créditos iniciais, status calculado, pagamento manual, trancar/destrancar/cancelar e listagem por aluno.
- `python3 -m pytest -q tests/`: **9 passed / 90 failed**, 18.00s. Saída completa em `pytest-ciclo-1.log` nesta pasta.
- `bash longrun/2026-10-05-academia-v1/verificar-limites.sh`: **LIMITES OK**, hash a768b39fe2101c18, 99 testes.
- Verificação adicional real pelo harness: pasta/configuração criadas, pedido sem token rejeitado antes de validar corpo, aluno/código/matrícula preservados depois de reiniciar o servidor.

## Falta
- Aulas/ocorrências, reservas concorrentes, cancelamento, espera, créditos e presença.
- Check-in/reativação; biblioteca/ficha/meu treino; 12 SVGs e páginas de exercícios; avaliação física.
- Conversa completa na ordem §11; tarefas/rodar e avisos de vencimento (a parte automática de matrículas está pendente).
- Campanhas, LGPD (inclusive /dados), Raio-X; demais cadastros e backup.
- Evolution/Telegram apenas contra servidores falsos; Docker, .env.exemplo, README Deploy na VPS, tools/render-exercicios sem executar; páginas / e /equipe.
- Teste de deduplicação de aluno ainda falha ao chegar em /dados (LGPD não implementada); persistência de reservas e teste de semente completo aguardam respectivas rotas. Não confundir com falha da persistência básica já verificada.

## Como retomar
1. Ler goal → state → plan → canal → fim de progress/failures. Spec e conftest já foram lidos neste ciclo.
2. Ler `src/store.py`, `src/domain.py`, `src/server.py` e tests/test_aulas.py; implementar ocorrências/reservas primeiro, usando Academia.ativa para autorização de matrícula na data da aula.
3. Rodar `python3 -m pytest -q tests/ > longrun/2026-10-05-academia-v1/pytest-ciclo-2.log 2>&1` e ler só `tail -n 30` desse log; depois verificar-limites.sh.
4. Atualizar registros, sem commit. Não executar render-exercicios, nem APIs reais/rede externa.
