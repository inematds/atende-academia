# Decisões — aguardando resposta do dono

Cada item tem uma **proposta padrão já aplicada** na spec e nos testes. Responder "ok em tudo" já destrava a execução (`longrun/2026-10-05-academia-v1/congelar.sh`). Se mudar algo marcado ⚠ (afeta o contrato), edite `docs/ESPECIFICACAO.md` e os testes **antes** de congelar o hash.

| # | Decisão | Proposta padrão (aplicada) | Por quê |
|---|---|---|---|
| 1 | Nome do projeto / repo | `atende-academia` (pasta e futuro repo `inematds/atende-academia`) | regra: repo = nome da pasta |
| 2 ⚠ | Linguagem | **Python 3, só biblioteca padrão** (`http.server` + `sqlite3`) | mesmo molde do atende-clinica (93/93); testes caixa-preta não prendem a linguagem, mas `verificar-limites.sh`, `goal.md` e `prompt.md` assumem Python |
| 3 | Canais | chat web + **WhatsApp pela Evolution API** (simulado quando não configurado); equipe pelo **Telegram** e pela página `/equipe` | igual ao atende-clinica (decisão do Nei em 05/10) |
| 4 ⚠ | Cobrança | **só status manual** `pago/pendente` marcado pela equipe + aviso de vencimento; nenhum Pix, cartão, PSP ou Pix Automático (§3.3, §16) | PSP = portão humano; o Raio-X recomenda plano/assinatura só depois da agenda organizada |
| 5 ⚠ | Trava de campanha (CREF/CONFEF) | **mínimo comum seguro**: `promessa_resultado` (garantido, 100%...) e `antes_depois` (§13); **sem citar artigo** | não há pesquisa do CREF/CONFEF no Raio-X (só CFM, CFO, COFFITO). **Confirmar as regras do conselho antes de publicar qualquer campanha**; se houver mais vedações, entram como códigos novos na tabela da §13 |
| 6 ⚠ | Avaliação física | dado **sensível** (LGPD art. 11): só rota [R], em `/dados`, nunca pela conversa, apagado no `DELETE` (§8, §15). Base legal sugerida: consentimento específico no formulário de matrícula | o Raio-X só tem a leitura para clínica (tutela da saúde); educador físico é profissão de saúde, mas a base precisa ser confirmada pelo dono/advogado |
| 7 ⚠ | Reativação ("sumiu há N dias") | é **marketing**: só com `consentimento_marketing: true` (§5, §12). Vencimento, espera, aula cancelada e lembrete de avaliação = execução do contrato (sem consentimento, respeitam PARAR) | academia não é serviço de saúde: legítimo interesse até caberia, mas a proposta conservadora evita discussão. Mudar = editar §5/§12 e `test_reativacao_apos_inatividade` |
| 8 ⚠ | Falta automática | reserva sem check-in no dia, depois que a aula terminou, vira `falta` no `tarefas/rodar`; a equipe pode corrigir (§4.6) | é o nº 1 do Raio-X (falta sem aviso) e dá o `falta_pct` sem trabalho manual |
| 9 ⚠ | Cancelamento tardio | dentro do prazo (`cancelamento_prazo_horas`, padrão 2 h) = `cancelada`; depois = `cancelada_tarde`: libera a vaga, dispara a espera, **não devolve crédito** avulso e **não** conta como falta (§4.3, §4.5) | política escrita e avisada, como pede o módulo "Agenda cheia"; penalidade financeira fica fora (cobrança é manual) |
| 10 ⚠ | Check-in | por **código numérico** do aluno (gerado, 4–8 dígitos) na recepção ou pelo chat (`cheguei`); **um por dia**; exige matrícula ativa (§5); sem catraca/leitor | catraca é hardware/integração = fora do v1 |
| 11 ⚠ | Animações dos exercícios | **12 SVGs desenhados pelo agente** (figura esquemática, animação **só por CSS** `@keyframes` com durações 1/2/4 s, **sem SMIL**, ≤ 60 KB, sem script) em `web/exercicios/`; MP4 só por `tools/render-exercicios` (HyperFrames local, composição só CSS sem GSAP/CDN, passo de build fora do loop) (§7) | sem API de imagem/vídeo; o render do HyperFrames busca quadro a quadro pelos adaptadores CSS/WAAPI (`document.getAnimations()`) e **não tem adaptador SMIL** (conferido no código do pacote, versões 0.7.109 e 0.8.86 — `docs/VALIDACAO.md`); coerente com o atende-fisioterapia; o pytest confere forma e o verificador nível 4 confere que se mexe |
| 12 ⚠ | Chat × avaliação física | o chat **não marca** avaliação (responde "fale com a recepção"); marcar é pela página/API (§8, §11) | reduz fluxos no v1; entra na v2 se o dono quiser |
| 13 ⚠ | Raio-X | não existe pacote `academia`: usa o **modelo genérico `servicos`** e exporta só ids que existem nele; `atendimentos_mes` = check-ins, `falta_pct` = faltas em aula coletiva, `ocupacao_pct` = vagas ocupadas ÷ oferecidas, `clientes_novos_mes` = primeiras matrículas, `retorno_atual_pct` = renovação em ±30 dias, `atendimentos_mes_recorrente` = check-ins ÷ ativos (§14) | cada mapeamento é **premissa** (ver `docs/MAPA-RAIO-X.md`); `alunos_ativos` e `cancelamentos_mes` saem como `indicadores`, fora do acompanhamento |
| 14 ⚠ | Trancamento | `trancar` **não estende** o `fim` (§3.3) | regra simples e testável; estender exige guardar dias trancados — v2 |
| 15 ⚠ | Equipe cancela uma aula | reservas viram `cancelada_pela_academia`, crédito devolvido, mensagem `aula_cancelada` a todos (§4.6) | professor doente é rotina; sem isso a falta automática puniria o aluno |
| 16 ⚠ | Alerta de saúde no chat | palavras da §11 (dor forte, dor no peito, falta de ar, desmaio, tontura, lesão, machuquei, torci, sangramento, infarto) → "pare, chame 192, avise o professor" + fila humana `alta` | molde da emergência do atende-clinica; conferir a lista com a academia-alvo |
| 17 | Quem executa | **headless: `loop-longrun.sh` com Codex `gpt-6-astra`** (`CODEX_ARGS` libera socket local). Alternativa: `/goal` no Codex TUI ou no Claude Code | rota testada no atende-clinica e nos kits reserva-* |
| 18 | Tetos | 20 ciclos × 30 min, 8 GB por ciclo, parar após 3 ciclos sem avanço | 99 testes + 12 SVGs: mais trabalho que o atende-clinica (93 em 7 ciclos); cabe com folga |
| 19 | GitHub / VPS | **não criar agora**; deploy na VPS pelo dono com o README; repo local | ação externa → confirmar |
| 20 | Idioma | só PT no v1 | EN/ES depois, pelo processo trilíngue do WiFi |

## Perguntas que só você responde

- Tem uma **academia real** para o piloto (grade, planos, professores, salas, FAQ verdadeiros)? Se sim, eu troco o `exemplos/academia.json` (o fixture dos testes continua o de exemplo).
- Isto é **produto para implantar** (via kit do Raio-X) ou **projeto aberto/curso**? Muda o que vem depois do v1 (guia, licença), não o v1.
- **MP4 no WhatsApp:** a Evolution baixa o vídeo pela URL pública (`PUBLIC_URL/exercicios/<id>.mp4`), então o v1 exige HTTPS público para esse caminho. Sem isso o aluno recebe o link da página (que também funciona no navegador do celular). Quer os MP4 gerados já no v1 (precisa Node + Chromium na máquina de build) ou deixa só o link?
- **CREF/CONFEF:** quais regras de publicidade a academia já segue? (decisão 5 — eu acrescento códigos na trava.)
- Quer a **página da equipe** só funcional (padrão) ou já com o visual INEMA?
- Plano de **aulas avulsas**: o crédito vale por reserva (padrão) ou por check-in?
