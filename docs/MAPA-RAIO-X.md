# Como o Raio-X de Margem alimenta este projeto

Fonte: `~/projetos/raio-x-margem`. **Não há pacote `academia`** nos setores (há `clinica`, `salao`, `restaurante`, `hotel` e a base `servicos`). O atende-academia usa o modelo genérico **`setores/servicos.js`** ("Serviços com agenda": hora marcada e cliente que volta) com as receitas `docs/modulos/servicos-agenda.md`, `cobranca.md`, `aquisicao.md` e `marketing-local.md`. A pesquisa do setor (`docs/setores/servicos-pesquisa-2026-10.md`) cobre clínicas e salões; para academia só lista o CNAE 9313-1/00 (condicionamento físico) como fonte de leads. **Nenhum número de mercado de academia aparece no Raio-X** — os de falta (5–25 % clínica; 14–17 % salão, EUA) são de outros perfis e ficam como premissa a medir na própria academia.

## Vazamentos do pacote `servicos` × o que o atende-academia ataca

| Vazamento (id no Raio-X) | Peça no v1 | Seção da spec | Medido? |
|---|---|---|---|
| `faltas` — falta sem aviso (nº 1 do modelo; receitas `agenda-cheia`, `cobranca`) | reserva de vaga com limite, prazo de cancelamento escrito, lista de espera com oferta automática, **falta automática** (reserva sem check-in), equipe cancela aula com aviso | 4.2–4.6, 5 | sim: `falta_pct` nas aulas coletivas |
| `ociosidade` — horário que nunca foi agendado (`agenda-cheia`, `marketing-local`) | grade visível no chat ("quais aulas tem"), reserva pelo chat, ocupação por aula | 4.1, 11, 14 | sim: `ocupacao_pct` = vagas ocupadas ÷ oferecidas |
| `retorno` — cliente que não volta no prazo (`agenda-cheia`, `aquisicao`) | aviso de vencimento do plano, **reativação** por inatividade (N dias sem check-in, com consentimento), renovação medida | 3.3, 5, 14 | sim: `retorno_atual_pct` = renovação em ±30 dias do fim |
| `mao_de_obra` — recepção presa marcando à mão (`agenda-cheia`) | reserva, cancelamento, check-in, "meu plano", "meu treino" e FAQ pelo chat; fila humana só para o que o bot não resolve | 5, 6, 11, 21 | não (o Raio-X pergunta `horas_agenda_manual_semana` ao dono) |
| `marketing` — anúncio pagando por quem já é cliente (`marketing-local`, `aquisicao`) | base própria consentida (`consentimento_marketing`), campanhas com trava e opt-out, reativação | 12, 13 | não (só habilita) |
| `adicional` — adicional que ninguém oferece | **fora**: avaliação física é serviço, mas sem preço/venda no v1 | 16 | — |
| `plataforma` — marketplace cobrando de quem já é seu | **fora**: academia raramente vende por intermediário; nada a medir no v1 | 16 | — |
| `pagamentos`, `antecipacao`, `caixa` — taxas, antecipação, juros | **fora**: cobrança é só status manual (decisão 4); extrato é do dono | 16 | — |

## O que vai para o Painel de Recuperação (ids reais de `setores/servicos.js`)

| id | como o sistema calcula | premissa |
|---|---|---|
| `atendimentos_mes` | nº de check-ins no mês | "atendimento" de academia = visita (check-in), não aula |
| `falta_pct` | faltas ÷ (presenças + faltas) nas reservas de aula coletiva do mês | só aulas com reserva; musculação livre não entra |
| `ocupacao_pct` | reservas ativas ÷ soma das vagas de todas as ocorrências do mês | ocupação de **aula**, não da sala de musculação |
| `clientes_novos_mes` | alunos cuja primeira matrícula começa no mês | — |
| `retorno_atual_pct` | % das matrículas que vencem no mês com outra matrícula começando em ±30 dias | "voltar no prazo" = renovar |
| `atendimentos_mes_recorrente` | check-ins ÷ alunos ativos no último dia do mês | frequência média; o Raio-X usa como "atendimentos de quem volta" |

Não medidos, ficam como estavam no acompanhamento: `ticket_medio`, `faturamento`, `margem_contrib_pct`, metas (`*_meta_pct`), `horas_disponiveis_mes`, `receita_hora`, pagamentos e marketing. `alunos_ativos` e `cancelamentos_mes` saem como `indicadores` na rota (não há id no pacote; não entram no arquivo do painel).

## Regras que viraram trava testável

- **LGPD:** aviso de vencimento, espera, aula cancelada e lembrete de avaliação = execução do contrato (art. 7º, V); reativação e campanha = consentimento (art. 7º, I); "PARAR" bloqueia tudo que é automático; exportar e anonimizar (art. 18). Avaliação física = dado sensível (art. 11): só [R], nunca pela conversa, apagada no `DELETE`.
- **Publicidade:** trava mínima (promessa de resultado, antes e depois) sem citar CREF/CONFEF — não pesquisado no Raio-X (decisão 5 ⚠).
- **Bot não prescreve:** mostra a ficha do professor e explica só o catálogo; dor/alerta → 192 + professor + humano `alta`.

## Volta para o Raio-X

`GET /api/raiox?mes=` e `./atende raiox --acompanhamento` produzem `valores` com os ids acima no formato do `app/painel-motor.js` (`{tipo: "acompanhamento", pacote: "servicos", base, meses: [{mes, valores, obs: "atende-academia"}]}`). Ciclo: Raio-X mede o "antes" (4 semanas de agenda, como manda o módulo) → atende-academia implanta reserva + espera + reativação → o painel mostra o "depois" todo mês com número tirado do sistema.
