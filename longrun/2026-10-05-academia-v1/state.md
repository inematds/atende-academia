# Estado — atualizado 2026-10-19, ciclo 2

## Funciona
- Base `./atende serve --porta 0 --dados DIR`: primeira linha PORTA=<n>, bind padrão 127.0.0.1, JSON UTF-8, auth anterior à validação, SQLite/WAL com semente única e transações serializadas.
- Alunos, planos e matrículas: normalização/deduplicação, busca, código único, vigência inclusiva, pagamento manual, trancar/destrancar/cancelar e seleção da matrícula ativa.
- Aulas: ocorrências por dia/período, feriados, nomes dos catálogos, ordem e disponibilidade; reservas com validações na ordem contratada, créditos e concorrência pela última vaga.
- Cancelamento no prazo/fora do prazo, devolução à matrícula original, presença/falta manual, cancelamento pela academia com devolução e avisos simulados; persistência de reservas após reinício.
- Lista de espera: criar/listar, primeira oferta pendente por ocorrência respeitando nao_contatar, persistência de ofertado; /api/saida com caixa simulada. Confirmação da oferta pelo chat ainda ausente.
- Versão 0.2.0. Domínio de aulas em src/classes.py, conectado a src/server.py.
- Suíte completa: **20 passed / 79 failed**, 19.58s; log pytest-ciclo-2.log. Onze testes adicionais passam em relação ao ciclo 1, incluindo concorrência, créditos e persistência.
- Verificador: **LIMITES OK** (hash a768b39fe2101c18, 99 testes, escopo ok, sem API/rede).

## Falta
- Check-in/reativação e presença automática por tarefas; avisos de vencimento e demais tarefas.
- Biblioteca/ficha/meu treino; 12 SVGs CSS manuais e páginas; avaliação física.
- Conversa completa na ordem §11, inclusive confirmação da oferta de espera (não implementar atalho isolado que ignore saúde/parar/humano).
- Campanhas, LGPD, Raio-X, demais cadastros e backup; Evolution/Telegram com servidores falsos; Docker/.env.exemplo/README Deploy na VPS/render-exercicios e páginas / e /equipe.
- Dois testes de aulas dependem dos próximos módulos: test_lista_de_espera_oferece_reserva_e_lotada chega ao chat ausente; test_presenca_manual_e_automatica chega ao check-in ausente.
- Caixa de saída ainda somente simulada; integração e reenvio serão implementados no módulo Evolution. Não usar com serviços reais neste loop.

## Como retomar
1. Ler goal → state → plan → canal → fim de progress/failures. Spec completa e conftest foram lidos neste ciclo.
2. Ler src/classes.py, src/domain.py e testes de check-in/tarefas (localizar nomes com rg --files tests); implementar check-in e reativação, com presença automática e aviso de vencimento necessários às verificações.
3. Seguir biblioteca/fichas, SVGs, avaliação e conversa na ordem contratada; reutilizar Classes.reserve/change nas ações do chat.
4. Rodar suíte completa para arquivo, ler tail -n 30 e executar verificar-limites.sh; atualizar registros. Sem commit/rede/API real e sem executar render-exercicios.
