# Especificação v1 — atende-academia (contrato congelado)

> Este arquivo é **protegido** durante a execução longa: o agente implementa contra ele e não o altera.
> Os testes em `tests/` verificam exatamente o que está aqui. Mudança de contrato = humano edita, recongela o hash e reinicia o longrun.

## 0. O que é

Sistema de atendimento ao aluno para **uma academia ou estúdio pequeno** (musculação, spinning, pilates, funcional): alunos e planos, matrícula com vencimento e cobrança como **status manual**, grade de aulas coletivas com reserva de vaga, lista de espera e falta, check-in e frequência com mensagem de reativação, ficha de treino montada pelo professor, **explicação animada de exercícios** (SVG animado; MP4 no WhatsApp), avaliação física agendada, FAQ, passagem para humano, campanhas com trava de publicidade e LGPD, e exportação de números para o **Painel de Recuperação do Raio-X de Margem** (pacote `servicos`).

Canais: **chat web**, **WhatsApp pela Evolution API** (seção 20) e caixa de saída **simulada** quando a Evolution não está configurada. Equipe interna atende pelo **Telegram** (seção 21) e pela página da equipe. Cadastros (seção 18), backup do banco (seção 19) e entrega em **Docker** para VPS (seção 22).

O bot **não prescreve** treino nem exercício: só mostra a ficha que o professor montou e explica os exercícios que estão no catálogo.

## 1. Execução

- Ponto de entrada: arquivo executável `./atende` na raiz do repo.
- `./atende serve --porta N --dados DIR [--host H]`
  - `--porta 0` = porta livre escolhida pelo sistema. A **primeira linha** do stdout é `PORTA=<n>` (com flush), impressa quando o servidor já aceita conexões.
  - Escuta em `--host` (padrão `127.0.0.1`; no Docker, `0.0.0.0` passado pelo comando do container — nunca escrito no código).
  - `DIR` é criado se não existir. `DIR/academia.json` = configuração (seção 2). Se não existir, copiar `exemplos/academia.json`.
  - Todo o estado persiste em `DIR/` (ex.: SQLite). Reiniciar com o mesmo `DIR` mantém tudo.
  - O servidor atende **várias conexões ao mesmo tempo** (ex.: `ThreadingHTTPServer`); os testes de concorrência abrem 10 conexões simultâneas. A criação de reserva e de check-in é serializada (trava ou transação) para garantir as regras das seções 4 e 5.
- **Relógio:** variável de ambiente `ATENDE_AGORA` (`AAAA-MM-DDTHH:MM`, hora local da academia, sem fuso) fixa o "agora" do processo. Sem ela, usa o relógio real. **Hoje** = a data de "agora". Datas no contrato são `AAAA-MM-DD`; horas `HH:MM`; instantes `AAAA-MM-DDTHH:MM`.
- `./atende raiox --dados DIR --mes AAAA-MM --acompanhamento ARQ` (seção 14).
- `./atende backup` / `./atende restaurar` (seção 19).
- `PUBLIC_URL` (ex.: `https://academia.exemplo.com.br`, sem barra final): endereço público do sistema, usado nos links enviados ao aluno (seção 7). Sem ela, os links são relativos (`/exercicios/<id>`).
- `EXERCICIOS_MP4_DIR`: pasta de onde `GET /exercicios/<id>.mp4` é servido e onde o sistema procura o MP4 de um exercício (padrão `web/exercicios`, relativa à raiz do repo).
- Integrações externas **só** por variáveis de ambiente (seções 20–21). Sem elas, nenhuma chamada de rede sai do processo. Nenhuma URL externa, chave ou token escrito no código.

## 2. `academia.json`

```json
{
  "nome": "Academia Movimento",
  "token": "segredo",                   // exigido no header X-Token das rotas da equipe
  "passo_min": 30,                      // grade de horários da avaliação física
  "avaliacao_duracao_min": 30,
  "avaliacao_antecedencia_horas": 2,    // não oferece/aceita avaliação antes de agora + isto
  "avaliacao_lembrete_horas": 24,       // lembra a avaliação quando ela começa em até 24 h
  "reserva_antecedencia_dias": 7,       // reserva de aula só até hoje + 7 dias (inclusive)
  "cancelamento_prazo_horas": 2,        // cancelar até 2 h antes da aula = sem penalidade
  "inatividade_dias": 14,               // sem check-in há 14 dias → mensagem de reativação
  "vencimento_aviso_dias": 5,           // avisa o vencimento quando faltam até 5 dias
  "feriados": ["2026-10-12"],
  "horarios": { "seg": [["06:00","22:00"]], ..., "sab": [["08:00","12:00"]], "dom": [] },   // funcionamento
  "modalidades": [ { "id": "spinning", "nome": "Spinning" } ],
  "professores": [ { "id": "carla", "nome": "Carla", "avaliacao": true, "horarios": {...} | null } ],
  "salas": [ { "id": "sala1", "nome": "Sala 1" } ],
  "planos": [ { "id": "mensal", "nome": "Mensal", "preco": 129.90, "vigencia_dias": 30, "aulas": null } ],
  "grade": [ { "id": "spin-ter-7", "modalidade": "spinning", "professor": "diego", "sala": "sala1", "dia": "ter", "hora": "07:00", "duracao_min": 45, "vagas": 3 } ],
  "exercicios": [ { "id": "prancha", "nome": "Prancha", "apelidos": ["plank"], "grupo": "core", "passos": ["..."], "erros_comuns": ["..."], "cuidados": ["..."] } ],
  "faq": [ { "id": "estacionamento", "perguntas": ["tem estacionamento"], "resposta": "Temos estacionamento próprio." } ]
}
```

Dias da semana: `seg ter qua qui sex sab dom`. `planos[].aulas`: `null` = ilimitado dentro da vigência; inteiro = plano de **aulas avulsas** (créditos, seção 4.5). `professores[].avaliacao`: só quem tem `true` faz avaliação física; `horarios` do professor (mesmo formato de `horarios`) são as janelas em que ele faz avaliação; `null` = as janelas de funcionamento da academia.

`nome, token, passo_min, avaliacao_*, reserva_antecedencia_dias, cancelamento_prazo_horas, inatividade_dias, vencimento_aviso_dias, feriados, horarios` são lidos a cada início. `modalidades, professores, salas, planos, grade, exercicios, faq` só **semeiam** o banco na primeira vez (banco vazio); depois o banco é a fonte e se edita pela API (seção 18).

## 3. Alunos, planos e matrículas

### 3.1 Aluno
- `{id, nome, telefone, codigo, email, nascimento, consentimento_marketing, nao_contatar}`. `id` inteiro sequencial. `codigo` = código de check-in gerado pelo sistema: texto de 4 a 8 dígitos, único entre os alunos; devolvido na criação e nas listagens; nunca muda.
- Telefone: aceita com ou sem `+55`, espaços, parênteses e hífen; normaliza para `+55DDNNNNNNNNN` (DDD + 8 ou 9 dígitos; contando só dígitos: 10 ou 11 sem o 55, 12 ou 13 com ele). Fora disso → inválido (400). Todas as respostas usam o telefone normalizado. Telefone já cadastrado → `POST /api/alunos` devolve 200 com o mesmo `{id, codigo}`.

### 3.2 Plano
- `{id, nome, preco, vigencia_dias, aulas, ativo}`. `GET /api/planos` (público) lista só os ativos, na ordem de cadastro. Plano inativo não aceita matrícula nova (422) e some do chat.

### 3.3 Matrícula
- `POST /api/matriculas {aluno_id, plano, inicio?}` → 201 `{id, aluno_id, plano, inicio, fim, status, pagamento, aulas_restantes}`. `inicio` padrão = hoje; pode ser passado ou futuro. **`fim = inicio + vigencia_dias − 1`** (vigência inclusiva nas duas pontas: plano de 30 dias iniciado em 10/09 termina em 09/10). `aulas_restantes` = `planos[].aulas` na criação (`null` em plano ilimitado). Aluno ou plano inexistente → 404; plano inativo → 422. Um aluno pode ter várias matrículas (renovação antecipada).
- `pagamento` ∈ `pendente` | `pago`; nasce `pendente`; `POST /api/matriculas/{id}/pagamento {pago: bool}` → 200 com a matrícula. **Só status manual**: nenhuma cobrança, Pix ou PSP no v1.
- Situação guardada: `ativa` (padrão), `trancada` (`POST /api/matriculas/{id}/trancar` → 200), de volta a `ativa` (`POST .../destrancar` → 200; trancar **não** estende o `fim` no v1), `cancelada` (`POST .../cancelar` → 200; grava `cancelada_em` = hoje; irreversível: qualquer ação sobre matrícula cancelada → 409). `trancar` sobre matrícula já trancada e `destrancar` sobre matrícula não trancada → 409.
- **`status`** nas respostas (calculado): `cancelada` se cancelada; senão `trancada` se trancada; senão `vencida` se `hoje > fim`; senão `ativa`.
- **Matrícula ativa numa data D** = situação `ativa` e `inicio ≤ D ≤ fim`. Se houver mais de uma, vale a de maior `fim` (desempate: maior `id`). É ela que autoriza reserva (seção 4) e check-in (seção 5) e que consome créditos.
- **Motivo** de recusa (422 `{"motivo": ...}`) quando não há matrícula ativa em D, avaliado nesta ordem sobre as matrículas **não canceladas** do aluno: nenhuma → `sem_matricula`; alguma cobre D mas está trancada → `matricula_trancada`; nenhuma cobre D (vencidas ou ainda não iniciadas) → `matricula_vencida`.
- `GET /api/alunos/{id}/matriculas` [R] → `{"matriculas": [...]}` em ordem de `id`.
- **Aviso de vencimento** (`POST /api/tarefas/rodar`, seção 12): matrícula com situação `ativa` cujo `fim − vencimento_aviso_dias ≤ hoje ≤ fim` e que ainda não recebeu aviso → mensagem `tipo: "vencimento"` com `referencia_id` = id da matrícula; texto contém o nome do plano e `DD/MM` do `fim`. **Uma vez por matrícula.** Não depende de `consentimento_marketing`; aluno `nao_contatar` não recebe (a mensagem não é criada).

## 4. Aulas coletivas

### 4.1 Grade e ocorrências
- `grade[]` = aulas **semanais**: `{id, modalidade, professor, sala, dia, hora, duracao_min, vagas, ativo}`.
- **Ocorrência** = par `(aula_id, data)` em que `data` cai no `dia` da semana da aula, `data` não está em `feriados` e a aula está ativa. `inicio = data + hora`, `fim = inicio + duracao_min`. A equipe pode **cancelar** uma ocorrência (4.6); ela continua listada com `cancelada: true`.
- `GET /api/aulas?data=AAAA-MM-DD` (público) → 200 `{"aulas": [{aula_id, data, inicio, fim, modalidade, professor, sala, vagas, reservadas, livres, cancelada}]}` com **todas** as ocorrências do dia (inclusive as já passadas e as canceladas), ordenadas por `inicio`, depois por `aula_id`. `modalidade`, `professor` e `sala` são os **nomes**; `reservadas` = reservas ativas (4.2); `livres = vagas − reservadas` (0 quando cancelada). Dia sem ocorrência (domingo, feriado) → `[]`.
- `GET /api/aulas?de=AAAA-MM-DD&ate=AAAA-MM-DD` [R] → o mesmo, para o período (inclusivo nas duas pontas), na mesma ordem (por `inicio`, depois `aula_id`).

### 4.2 Reserva
- `POST /api/reservas {aluno_id, aula_id, data}` [R] → 201 `{id, aluno_id, aula_id, data, inicio, status: "reservada", aulas_restantes}` (`aulas_restantes` da matrícula usada; `null` em plano ilimitado).
- Ordem das verificações: 401 → aluno ou aula inexistente **404** → **422** `{"motivo": m}` com `m` ∈ `sem_aula` (não é ocorrência: dia errado, feriado, aula inativa ou ocorrência cancelada), `aula_passada` (`inicio ≤ agora`), `antecedencia` (`data > hoje + reserva_antecedencia_dias`; `hoje + 7` ainda vale), `sem_matricula` | `matricula_trancada` | `matricula_vencida` (3.3, avaliado na `data` da aula), `sem_aulas` (plano avulso com `aulas_restantes = 0`) → **409** `{"motivo": "ja_reservada"}` (o aluno já tem reserva ativa nessa ocorrência) → **409** `{"motivo": "lotada"}` (`reservadas ≥ vagas`).
- Reserva **ativa** = status `reservada`, `presente` ou `falta` (ocupa vaga). `cancelada`, `cancelada_tarde` e `cancelada_pela_academia` liberam a vaga.
- **Concorrência:** 10 pedidos simultâneos para a última vaga → exatamente um 201, os outros 409 `lotada`.
- `GET /api/reservas?data=AAAA-MM-DD` [R] → 200 `{"reservas": [{id, aluno_id, nome, telefone, aula_id, data, inicio, modalidade, status}]}` com todos os status, ordenadas por `inicio`, depois por `id`. Aceita também `?de=&ate=` (inclusivo) e `?aluno_id=`.

### 4.3 Cancelamento
- `POST /api/reservas/{id}/cancelar` [R] → 200 `{status}`: `cancelada` se `agora + cancelamento_prazo_horas ≤ inicio` (cancelar exatamente 2 h antes ainda é dentro do prazo), senão `cancelada_tarde`. Os dois liberam a vaga e disparam a lista de espera (4.4). Reserva que não está `reservada` → 409.

### 4.4 Lista de espera
- `POST /api/espera {aluno_id, aula_id, data}` [R] → 201 `{id}` (404 para aluno/aula inexistente; a ocorrência não precisa estar lotada). `GET /api/espera?data=` [R] → `{"espera": [{id, aluno_id, aula_id, data, status}]}` em ordem de `id`.
- Quando uma vaga abre (4.3 ou 4.6), o **primeiro** pedido `pendente` da mesma `(aula_id, data)` (ordem de criação) cujo aluno não esteja `nao_contatar` recebe mensagem `tipo: "espera"` contendo `DD/MM`, `HH:MM` da aula e `1`; o pedido vira `ofertado` (não recebe outra oferta). Pedido de outra data ou aula não recebe.
- Resposta `1`/`sim` do aluno (seção 11, pendência): cria a reserva pelas regras de 4.2 — resposta contém `reservad`; se já lotou de novo, contém `lotada`; se o aluno não tem matrícula ativa, contém `plano`.

### 4.5 Aulas avulsas (créditos)
Matrícula de plano com `aulas = N`: cada reserva (API ou chat) **desconta 1** de `aulas_restantes` na criação; `cancelada` (dentro do prazo) **devolve 1**; `cancelada_tarde`, `falta` e `presente` não devolvem; `cancelada_pela_academia` devolve 1. Com `aulas_restantes = 0` → 422 `sem_aulas`. Check-in não consome crédito.

### 4.6 Presença, falta e ocorrência cancelada
- `POST /api/reservas/{id}/presenca {compareceu: bool}` [R] → 200 `{status: "presente" | "falta"}`, a qualquer momento, sobre reserva `reservada`, `presente` ou `falta` (outros status → 409).
- **Falta automática** (`POST /api/tarefas/rodar`): toda reserva `reservada` cuja aula já terminou (`fim ≤ agora` da rodada) vira `presente` se o aluno tem check-in (seção 5) naquela `data`, senão `falta`. Regra escrita para o aluno: *reserva sem check-in no dia da aula conta como falta.*
- `POST /api/aulas/{aula_id}/ocorrencias/{data}/cancelar {motivo?}` [R] → 200 `{"canceladas": n}`: a ocorrência passa a `cancelada: true` (`livres: 0`, reservas novas → 422 `sem_aula`); reservas `reservada` viram `cancelada_pela_academia` (crédito devolvido) e cada aluno (não `nao_contatar`) recebe mensagem `tipo: "aula_cancelada"` contendo `DD/MM`, `HH:MM` e o nome da modalidade. Ocorrência inexistente → 404; já cancelada → 409.

## 5. Check-in e frequência

- `POST /api/checkins {codigo}` [R] → 201 `{id, aluno_id, nome, quando}` (`quando` = agora, `AAAA-MM-DDTHH:MM`). Código inexistente (ou de aluno anonimizado) → 404. Sem matrícula ativa em **hoje** → 422 `{"motivo": ...}` (3.3). Segundo check-in do mesmo aluno **no mesmo dia** → 200 com o mesmo `{id, ..., quando}` do primeiro (um check-in por dia).
- Pelo chat (seção 11): aluno conhecido manda `check in` / `cheguei` → mesma regra; resposta contém `check-in`.
- `GET /api/checkins?de=AAAA-MM-DD&ate=AAAA-MM-DD` [R] → 200 `{"checkins": [{id, aluno_id, nome, quando}]}` (inclusivo nas pontas), ordem de `quando`, depois `id`. Aceita `?aluno_id=`.
- **Reativação** (`POST /api/tarefas/rodar`): para cada aluno com matrícula ativa em hoje, `consentimento_marketing: true` e não `nao_contatar`: `ultimo` = instante (`quando`) do check-in mais recente; sem check-in nunca, `ultimo` = `inicio` da matrícula ativa às `00:00`. Se `hoje − data(ultimo) ≥ inatividade_dias` (14 dias exatos já contam) e não existe mensagem `reativacao` para o aluno criada **estritamente depois** de `ultimo` (`quando` da mensagem > `ultimo`; com relógio fixo, mensagem e check-in no mesmo minuto **não** bloqueiam) → mensagem `tipo: "reativacao"` cujo texto contém `treinar`. Ou seja, **uma por período de inatividade**: só volta a mandar depois de um novo check-in. Reativação é marketing: sem consentimento, não existe.

## 6. Treino

### 6.1 Biblioteca de exercícios
- Exercício: `{id, nome, apelidos, grupo, passos, erros_comuns, cuidados, ativo, svg: bool}`. `svg` = existe `web/exercicios/<id>.svg` (seção 7).
- `GET /api/exercicios` (público) → `{"exercicios": [...]}` só os ativos, na ordem de cadastro (a do `academia.json` na semente). `GET /api/exercicios/{id}` → 200 o exercício (inclusive inativo) ou 404.
- Equipe (seção 18): `POST /api/exercicios {id, nome, apelidos?, grupo?, passos, erros_comuns?, cuidados?}` → 201 (`id` repetido → 409; `passos` vazio → 422); `PUT` parcial → 200; `DELETE` → 200 `{"ativo": false}` (some da lista pública, do chat e não entra em ficha nova; fichas existentes continuam).

### 6.2 Ficha do aluno
- `PUT /api/alunos/{id}/ficha {treinos: [{nome, itens: [{exercicio, series, repeticoes, carga?, descanso_s?}]}]}` [R] → 200 com a ficha (substitui a anterior). `treinos` com pelo menos 1 treino com pelo menos 1 item; `exercicio` inexistente ou inativo → 422; aluno inexistente → 404. `series` e `repeticoes` inteiros > 0; `carga` texto livre (ex.: `"20 kg"`) ou ausente; `descanso_s` inteiro ou ausente.
- `GET /api/alunos/{id}/ficha` [R] → 200 `{treinos: [...]}` ou 404 se não há ficha. `DELETE /api/alunos/{id}/ficha` → 204.

### 6.3 "Meu treino de hoje" (chat)
- Treino do dia = `treinos[k]`, com `k = (nº de check-ins do aluno em dias **anteriores** a hoje) mod nº de treinos` (primeiro dia → o primeiro treino; depois roda em sequência).
- Resposta: primeira linha `Treino <nome>`; depois uma linha por item: `- <nome do exercício>: <series>x<repeticoes>` + `, <carga>` se houver + `, descanso <descanso_s> s` se houver. Termina com a frase `Para ver como faz, peça: explica <nome do exercício>` (um exemplo com o primeiro item).
- Verificado **nesta ordem**: sem matrícula ativa hoje → resposta contém `plano` e `recepção` (antes de olhar a ficha); senão, sem ficha → contém `ficha` e `professor`; senão, o treino do dia acima.

## 7. Explicação animada de exercícios

### 7.1 SVG animado (arquivo por exercício)
Para **todo exercício do catálogo de exemplo** (`exemplos/academia.json` = fixture dos testes) existe `web/exercicios/<id>.svg`. Ids obrigatórios (12): `agachamento, flexao, prancha, remada, supino, terra-bastao, afundo, elevacao-pelvica, abdominal, desenvolvimento, puxada, polichinelo`. Regras de cada arquivo, verificadas pelos testes sem navegador:
- XML válido (`xml.etree`), raiz `svg` no namespace `http://www.w3.org/2000/svg`, com `viewBox` definido;
- `<title>` com texto em português (não vazio);
- **animação só por CSS**, dentro de `<style>` no próprio SVG: pelo menos um `@keyframes` e pelo menos um elemento com `animation` (ou `animation-name`) aplicada; **loop**: a palavra `infinite` em pelo menos uma animação (`animation-iteration-count: infinite` ou no atalho `animation`); toda duração (`animation-duration`, ou o **primeiro** tempo do atalho `animation`) ∈ {`1s`, `2s`, `4s`} (ou `1000ms`, `2000ms`, `4000ms`) — divisores dos 4 s do MP4 (7.4), para o vídeo fechar o ciclo. O movimento é a figura humana esquemática executando o exercício;
- **sem SMIL** (`<animate`, `<animateTransform`, `<animateMotion`, `<set`): o render do HyperFrames avança só animação CSS/WAAPI (7.4); SMIL não é pausado nem buscado e sairia fora de fase no MP4;
- **sem `<script`**, sem `<image`, sem `<foreignObject`, sem `@import`; sem `http` fora dos valores dos atributos `xmlns`/`xmlns:*`; todo `href`/`xlink:href` começa com `#`; todo `url(` aponta para `#` (nada externo);
- tamanho ≤ 60 KB (61 440 bytes).
A prova de que **se mexe** (dois quadros em instantes diferentes diferem) é feita no nível 4 (`verificar-independente.py`), não no pytest.

Esqueleto de referência (um por exercício, com movimento próprio):
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400">
  <title>Prancha</title>
  <style>
    .tronco { transform-origin: 200px 300px; animation: segura 2s ease-in-out infinite; }
    @keyframes segura { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
  </style>
  <rect width="400" height="400" fill="#fff"/>
  <g class="tronco" fill="none" stroke="#222" stroke-width="8" stroke-linecap="round"><path d="M 80 300 L 300 300"/></g>
</svg>
```

### 7.2 Páginas e arquivos
- `GET /exercicios/{id}` (público) → 200 HTML com `<h1>` = nome, `<ol>` com um `<li>` por passo (na ordem), os cuidados e, se houver SVG, referência a `/exercicios/{id}.svg` (`<img src>` ou `<object data>`). Exercício sem SVG (cadastrado pela equipe) → mesma página sem a animação e **sem nenhuma ocorrência de `.svg`** no HTML (nem ícone, nem link). Id inexistente no catálogo → 404.
- `GET /exercicios/{id}.svg` → 200 com o arquivo `web/exercicios/{id}.svg` e `Content-Type: image/svg+xml`; sem arquivo → 404.
- `GET /exercicios/{id}.mp4` → 200 `video/mp4` com `EXERCICIOS_MP4_DIR/<id>.mp4`; sem arquivo → 404.
- Caminho com `..` ou que saia da pasta (ex.: `/exercicios/../atende`) → 404 (400 também aceito); nunca serve arquivo fora de `web/exercicios` ou de `EXERCICIOS_MP4_DIR`.

### 7.3 Pela conversa
Pedido de exercício (seção 11): resposta **em uma mensagem** com: nome do exercício na primeira linha; passos numerados `1. ...`, `2. ...`; uma linha `Cuidado: <primeiro cuidado>` (se houver); última linha `Veja a animação: <link>` com `<link>` = `{PUBLIC_URL}/exercicios/<id>` (ou `/exercicios/<id>` sem `PUBLIC_URL`). Exercício sem SVG → sem a última linha.

**WhatsApp não mostra SVG.** Com a Evolution configurada (seção 20), a resposta de exercício é enviada assim:
- se existe `EXERCICIOS_MP4_DIR/<id>.mp4` **e** `PUBLIC_URL` está definida → `POST {EVOLUTION_URL}/message/sendMedia/{EVOLUTION_INSTANCIA}` com `{"number": "<dígitos com 55>", "mediatype": "video", "media": "{PUBLIC_URL}/exercicios/<id>.mp4", "caption": "<a mesma mensagem de texto, sem a linha do link>"}` e **nenhum** `sendText` para essa resposta;
- senão → `sendText` com a mensagem de texto (inclusive a linha do link).

### 7.4 MP4 com HyperFrames (passo de build, fora do pytest e do loop)
`tools/render-exercicios [--ids a,b] [--saida DIR]` (Python 3, biblioteca padrão + `subprocess`) gera `DIR/<id>.mp4` (padrão `web/exercicios`) a partir de cada `web/exercicios/<id>.svg`:
1. Detecta o HyperFrames com `npx --no-install hyperframes --version`; se falhar (sem Node, sem `npx` ou sem o pacote), sai com código 2 e a mensagem `pulado: hyperframes não instalado` — **nunca baixa pacote sozinho** (instalar é passo do humano, depois do loop: `npm install hyperframes` na raiz do repo ou `npm install -g hyperframes`; `node_modules/`, `package.json` e `package-lock.json` já estão no `.gitignore`). `ffprobe` ausente → código 2 e `pulado: ffprobe não instalado`.
2. Para cada exercício, cria uma pasta temporária com `index.html` = composição HyperFrames **só CSS** (sem GSAP, sem `<script>`, sem CDN, sem referência externa): `<div id="root" data-composition-id="exercicio" data-start="0" data-width="720" data-height="720" data-duration="4">` contendo o SVG inline, com `#root svg { position:absolute; inset:0; width:100%; height:100% }` e `body { margin:0; background:#fff }`. `data-duration="4"` é obrigatório: com animação `infinite` o runtime não infere a duração.
3. Roda `npx --no-install hyperframes render <pasta> --output <DIR>/<id>.mp4 --fps 30` (render local por Chromium, **sem API, sem conta**; **sem `--strict`**: a composição só CSS não registra `window.__timelines` e o lint `missing_timeline_registry` é tolerado — medido em 05/10/2026, `docs/VALIDACAO.md` §0) e confere com `ffprobe`: 720×720, duração entre 3,5 e 4,5 s, **sem stream de áudio**.
4. Imprime uma linha por exercício (`ok <id> <duração>s` ou `falhou <id> <motivo>`); código 0 só se todos os pedidos passaram, 1 se algum falhou.

Por que só CSS: o render do HyperFrames **busca** cada quadro numa linha do tempo pausada (shim de tempo virtual + adaptadores que fazem `document.getAnimations()` → `currentTime` + `pause()`), então a animação CSS do SVG inline é avançada quadro a quadro de forma determinística; **SMIL não tem adaptador** (nada chama `pauseAnimations`/`setCurrentTime` do SVG) e só avançaria por coincidência do relógio do compositor, saindo fora de fase conforme o modo de captura. Por isso 7.1 proíbe SMIL e exige durações de 1, 2 ou 4 s (o ciclo fecha em 4 s). Documentado no README; conferido no `verificar-independente.py`.

## 8. Avaliação física

- Profissional = `professores[].avaliacao: true`. Janelas = `horarios` do professor ou, se `null`, `horarios` da academia. Horário candidato: começa no início de uma janela e anda de `passo_min`; vale se `[inicio, inicio + avaliacao_duracao_min)` cabe inteiro na janela.
- **Inválido (422)** se: não é candidato; dia em `feriados`; `inicio < agora + avaliacao_antecedencia_horas`; professor não faz avaliação ou está inativo. **Ocupado (409)** se sobrepõe (intervalos semiabertos) outra avaliação ativa do mesmo professor **ou uma ocorrência de aula da grade dele** (ele está dando aula).
- `GET /api/avaliacoes/horarios?data=AAAA-MM-DD[&professor=P]` (público) → `{"horarios": [{inicio, professor}]}` só válidos e livres, ordenados por `inicio`, depois `professor`. Professor inexistente → 404; professor que existe mas não faz avaliação (ou inativo) → `[]`.
- `POST /api/avaliacoes {aluno_id, inicio, professor?}` [R] → 201 `{id, aluno_id, professor, inicio, fim, status: "agendada"}`; sem `professor` = o primeiro livre por ordem de `id`; aluno/professor inexistente → 404. Dois pedidos simultâneos no mesmo horário/professor: um 201, o outro 409.
- `POST /api/avaliacoes/{id}/cancelar` → 200 `{status: "cancelada"}`. Avaliação ativa = `agendada` ou `realizada`.
- `POST /api/avaliacoes/{id}/resultado {peso_kg, altura_cm, gordura_pct?, medidas?: {…}, observacoes?}` → 200 `{status: "realizada", ...}`; `peso_kg` e `altura_cm` obrigatórios (422 se faltarem ou ≤ 0).
- `GET /api/alunos/{id}/avaliacoes` [R] → `{"avaliacoes": [{id, professor, inicio, fim, status, resultado | null}]}` em ordem de `inicio`, depois `id` (todos os status).
- **Dado sensível (LGPD art. 11):** resultado só por rota [R] e em `/dados`; o bot **nunca** devolve resultado de avaliação pela conversa; `DELETE /api/alunos/{id}` apaga os valores (seção 15).
- **Lembrete** (`tarefas/rodar`): avaliação `agendada` com `agora < inicio ≤ agora + avaliacao_lembrete_horas` e ainda sem lembrete → mensagem `tipo: "avaliacao"` contendo `DD/MM`, `HH:MM` e o nome do professor. Uma vez. Não depende de consentimento; `nao_contatar` não recebe.

## 9. Autenticação

Rotas marcadas **[R]** (equipe) exigem header `X-Token` igual a `academia.json.token`; sem ele ou errado → **401**, avaliado **antes** de qualquer validação do corpo (`POST {}` sem token → 401, não 400/422). Rotas públicas: `/`, `/equipe` (página; os dados vêm de rotas [R]), `/exercicios/...`, `/api/saude`, `GET /api/planos`, `GET /api/modalidades`, `GET /api/aulas?data=`, `GET /api/exercicios`, `GET /api/exercicios/{id}`, `GET /api/avaliacoes/horarios`, `POST /api/mensagens`. Webhooks têm segredo próprio (seções 20 e 21).

## 10. API HTTP

Corpos e respostas em JSON UTF-8; toda resposta JSON leva `Content-Type: application/json`. Id inexistente no caminho ou no corpo → 404. Campo obrigatório ausente ou com tipo errado → 400 (telefone inválido também é 400); regra de negócio violada → 422 `{"motivo": ...}`; conflito de estado ou de vaga → 409.

| Método e rota | Corpo | Resposta |
|---|---|---|
| `GET /api/saude` | — | 200 `{"ok": true, "versao": "<conteúdo de VERSION>"}` |
| `GET /api/planos` | — | 200 `{"planos": [{id, nome, preco, vigencia_dias, aulas}]}` só ativos, ordem de cadastro |
| `GET /api/modalidades` | — | 200 `{"modalidades": [{id, nome}]}` ordem de cadastro |
| `GET /api/aulas?data=D` | — | 200 (seção 4.1) |
| `GET /api/aulas?de=&ate=` [R] | — | 200 (seção 4.1) |
| `POST /api/alunos` [R] | `{nome, telefone, consentimento_marketing?, email?, nascimento?}` | 201 `{id, codigo}`; telefone já cadastrado → 200 com o mesmo `{id, codigo}`; telefone inválido → 400 |
| `GET /api/alunos?busca=T` [R] | — | 200 `{"alunos": [{id, nome, telefone, codigo, email, nascimento, consentimento_marketing, nao_contatar}]}`; `busca` casa parte do nome (sem acento, sem caixa) ou dígitos do telefone ou o `codigo` exato; sem `busca` = todos; sempre em ordem de `id` |
| `PUT /api/alunos/{id}` [R] | parcial | 200 com o aluno; telefone inválido → 400; telefone de outro aluno → 409 |
| `POST /api/matriculas` [R] e rotas de 3.3 | | (seção 3.3) |
| `POST /api/reservas` [R], `GET /api/reservas`, `.../cancelar`, `.../presenca` | | (seções 4.2, 4.3, 4.6) |
| `POST /api/espera` [R], `GET /api/espera` | | (seção 4.4) |
| `POST /api/aulas/{aula_id}/ocorrencias/{data}/cancelar` [R] | `{motivo?}` | (seção 4.6) |
| `POST /api/checkins` [R], `GET /api/checkins` [R] | | (seção 5) |
| `GET /api/exercicios`, `GET /api/exercicios/{id}` | — | (seção 6.1) |
| `PUT/GET/DELETE /api/alunos/{id}/ficha` [R] | | (seção 6.2) |
| `GET /api/avaliacoes/horarios`, `POST /api/avaliacoes` [R], `.../cancelar`, `.../resultado`, `GET /api/alunos/{id}/avaliacoes` | | (seção 8) |
| `POST /api/tarefas/rodar` [R] | `{agora?}` (padrão = relógio do processo; vale só para esta rodada) | 200 `{"enviadas": n, "reenviadas": n, "presencas": n}` (seção 12); idempotente: rodar de novo no mesmo instante → `enviadas: 0` |
| `GET /api/saida` [R] | — | 200 `{"mensagens": [{id, tipo, telefone, aluno_id, texto, referencia_id, status}]}` em ordem de criação. `tipo` ∈ `vencimento, reativacao, espera, aula_cancelada, avaliacao, campanha, humano` |
| `POST /api/mensagens` | `{telefone, texto}` | 200 `{"respostas": [texto, ...]}` (seção 11) |
| `GET /api/atendimento-humano` [R] | — | 200 `{"fila": [{id, telefone, nome, motivo, prioridade, status}]}` só os `aberto`, em ordem de `id`; `prioridade` ∈ `normal, alta` |
| `POST /api/atendimento-humano/{id}/responder` [R] / `.../encerrar` [R] | `{texto}` / — | 200 (seção 21) |
| `POST /api/campanhas` [R] | `{texto}` | 200 `{"enviadas": n}` ou 422 `{"violacoes": [codigos]}` (seção 13) |
| `GET /api/alunos/{id}/dados` [R] | — | 200 (seção 15) |
| `DELETE /api/alunos/{id}` [R] | — | 204; anonimiza (seção 15); `GET .../dados` depois disso → 200 já anonimizado |
| `GET /api/raiox?mes=AAAA-MM` [R] | — | 200 (seção 14) |
| cadastros [R] | | (seção 18) |

## 11. Conversa (`POST /api/mensagens`)

O texto é normalizado antes de decidir: minúsculas, sem acento, pontuação substituída por espaço, espaços repetidos colapsados (`check-in` → `check in`). "Contém" = substring do texto normalizado. Ordem de decisão:

1. **Alerta de saúde** — contém um destes: `dor forte`, `dor no peito`, `falta de ar`, `desmaio`, `desmaiou`, `tontura`, `lesao`, `machuquei`, `torci`, `sangrando`, `sangramento`, `infarto`. Resposta contém `pare`, `192` e `professor`; entra na fila humana com `prioridade: "alta"`. Não reserva nada.
2. **Parar** — texto normalizado, sem espaços nas pontas, igual a `parar`, `sair` ou `pare`: aluno fica `nao_contatar`; resposta contém `não vai mais receber`. Nenhuma mensagem de saída automática (vencimento, reativação, espera, aula cancelada, avaliação, campanha) vai mais para esse telefone; a resposta direta do bot e a de um humano continuam.
3. **Humano** — contém `atendente`, `humano` ou `falar com alguem`: fila humana `normal`; resposta contém `atendente`.
4. **Fluxo em andamento** (reserva ou cancelamento pelo chat, abaixo) consome a mensagem.
5. **Pendência**: se a última mensagem da **caixa de saída** (`/api/saida`) para o telefone foi `espera` sem resposta: `1`/`sim` → seção 4.4.
6. **Telefone desconhecido** pedindo algo de aluno (itens 7–13): pergunta o nome (resposta contém `nome`); a próxima mensagem vira o nome, o aluno é criado (`consentimento_marketing: false`) e a resposta contém `plano` e `recepção` (aluno novo ainda não tem plano).
7. **Check-in** — contém `check in`, `checkin` ou `cheguei`: seção 5; resposta contém `check-in` e `bom treino`; sem matrícula ativa → contém `plano` e `recepção`.
8. **Avaliação** — contém `avaliacao`: resposta contém `avaliação` e `recepção` (marcar é com a equipe). Nunca mostra resultado.
9. **Cancelar** — contém `cancelar` ou `desmarcar`: lista as reservas `reservada` futuras do aluno em ordem de `inicio`, `N) DD/MM HH:MM <modalidade>`, e espera o número; escolhido, cancela pela regra 4.3 (resposta contém `cancelad`; se foi `cancelada_tarde`, contém também `prazo`). Sem reserva futura → resposta contém `nenhuma reserva`.
10. **Reservar** — contém `reservar`, `reserva`, `agendar`, `marcar` ou `inscrever`: sem matrícula ativa hoje → `plano` e `recepção`. Senão lista as **5 primeiras** ocorrências com `livres > 0`, não canceladas, com `inicio > agora` e `data ≤ hoje + reserva_antecedencia_dias`, ordem de 4.1, linhas `N) DD/MM HH:MM <modalidade> com <professor>`; escolhido o número, cria a reserva (4.2; resposta contém `reservad`, `DD/MM` e `HH:MM`; se der 422/409 a resposta contém o motivo em palavras: `lotada`, `aulas`...). Nenhuma aula disponível → resposta contém `sem aulas`.
11. **Aulas** — contém `aula` ou `grade`: lista as ocorrências de **hoje (só futuras) e amanhã**, não canceladas, uma linha `DD/MM HH:MM <modalidade> com <professor> — <livres> vagas`, ordem de 4.1; nenhuma → contém `sem aulas`.
12. **Meu plano** — contém `plano`, `vencimento`, `vence`, `mensalidade` ou `matricula`: com matrícula ativa hoje → resposta contém o nome do plano, `DD/MM` do `fim` e `ativ`; sem ativa mas com alguma não cancelada → nome do plano, `DD/MM` e `vencid` (ou `trancad`); nenhuma → `plano` e `recepção`.
13. **Meu treino** — contém `treino` ou `ficha`: seção 6.3.
14. **Exercício** — contém o `nome` ou um `apelido` (normalizados) de um exercício ativo: seção 7.3. Mais de um casa → o de casamento mais longo; empate → o primeiro do catálogo.
15. **FAQ** — palavras significativas de alguma pergunta do FAQ (≥ 3 letras, excluídas estas: `que qual quais quem como onde quando para com sem por dos das nos nas uma uns umas voce voces vcs tem ter sao esta estao ele ela eles elas isso isto aqui ali ai`): se ≥ 60 % delas aparecem no texto, responde **exatamente** a `resposta` daquele item (só ela, uma mensagem). Mais de um item casa → o de maior %; empate → o primeiro do FAQ.
16. **Não entendi** — resposta contém `não entendi` e oferece `atendente`. Na **segunda** seguida sem entender, entra na fila humana (`normal`) automaticamente.

Nos fluxos (9 e 10): número inválido → repete as opções; `cancelar` dentro do fluxo de reserva → sai do fluxo (resposta contém `ok`). O estado do fluxo é por telefone e persiste. Para o aluno **conhecido** nenhuma resposta pede nome. O bot nunca inventa preço, plano, diagnóstico ou treino: fora do catálogo e do FAQ cai na regra 16.

## 12. Tarefas automáticas e caixa de saída

`POST /api/tarefas/rodar {agora?}` executa, nesta ordem: reenvio de `pendente` (seção 20), faltas automáticas (4.6), avisos de vencimento (3.3), lembretes de avaliação (8), reativação (5). `enviadas` = mensagens **criadas** nesta rodada (mesmo que o envio fique `pendente`); `reenviadas` = pendentes que viraram `enviado`; `presencas` = reservas marcadas nesta rodada. Idempotente para o mesmo instante.

| tipo | quando | exige `consentimento_marketing` | respeita `nao_contatar` |
|---|---|---|---|
| `vencimento` | 3.3 | não (execução do contrato) | sim |
| `espera` | 4.4 | não | sim |
| `aula_cancelada` | 4.6 | não | sim |
| `avaliacao` | 8 | não | sim |
| `reativacao` | 5 | **sim** | sim |
| `campanha` | 13 | **sim** | sim |
| `humano` | 21 | não | não (é resposta a quem escreveu) |

"Respeita `nao_contatar`" = a mensagem **não é criada** (não aparece em `/api/saida`). Base legal: aviso operacional = execução do contrato (LGPD art. 7º, V); reativação e campanha = consentimento (art. 7º, I). Academia não é serviço de saúde; só a avaliação física gera dado sensível (seção 8).

## 13. Campanhas e trava de publicidade

`POST /api/campanhas {texto}` envia só para alunos com `consentimento_marketing: true` e sem `nao_contatar`. Antes de enviar, valida o texto em minúsculas e sem acento (**pontuação mantida**, para `100%`). O `422` lista **todos** os códigos violados; qualquer violação → nada é enviado.

| Código | Detecta |
|---|---|
| `promessa_resultado` | `garantido`, `garantia de resultado`, `resultado garantido`, `100%` |
| `antes_depois` | `antes e depois` |

É o **mínimo comum seguro** (promessa de resultado e "antes e depois"). As regras específicas do CREF/CONFEF para publicidade de educação física **não foram pesquisadas no Raio-X**: não há artigo citado aqui de propósito; o dono confirma antes de publicar campanha (`docs/DECISOES-ABERTAS.md`, ⚠).

## 14. Exportação para o Raio-X (Painel de Recuperação)

`GET /api/raiox?mes=AAAA-MM` → `{"pacote": "servicos", "mes": "AAAA-MM", "valores": {...}, "indicadores": {...}}`, números arredondados a 1 casa (`round` half-even do Python é aceito; os testes toleram ±0,06):

`valores` usa **só ids que existem em `raio-x-margem/setores/servicos.js`**:
- `atendimentos_mes` = nº de check-ins com `quando` no mês (inteiro);
- `falta_pct` = reservas `falta` ÷ (`presente` + `falta`) × 100, entre as reservas com `data` no mês (0 se não houver);
- `ocupacao_pct` = reservas ativas (`reservada`, `presente`, `falta`) com `data` no mês ÷ soma de `vagas` de **todas** as ocorrências não canceladas do mês (aulas ativas, dias do mês inteiro menos feriados) × 100 (0 se não houver ocorrência);
- `clientes_novos_mes` = alunos cuja **primeira** matrícula (menor `inicio`, qualquer situação) tem `inicio` no mês;
- `retorno_atual_pct` = das matrículas não canceladas com `fim` no mês, % cujo aluno tem **outra** matrícula não cancelada com `inicio` entre `fim − 30` e `fim + 30` dias (inclusive) — renovação no prazo (0 se não houver `fim` no mês);
- `atendimentos_mes_recorrente` = `atendimentos_mes ÷ alunos_ativos` (0 se `alunos_ativos = 0`).

`indicadores` (próprios da academia, **não** vão para o acompanhamento): `alunos_ativos` = alunos com matrícula de situação `ativa` cuja vigência cobre o **último dia do mês**; `cancelamentos_mes` = matrículas com `cancelada_em` no mês.

`./atende raiox --dados DIR --mes M --acompanhamento ARQ`: lê `ARQ` (formato do `raio-x-margem/app/painel-motor.js`: `{tipo: "acompanhamento", pacote, cliente, base: {data, valores}, meses: [{mes, valores, obs}]}`), insere ou substitui o mês `M` com `valores` = os da rota acima **mesclados** sobre os valores do mês anterior (ou da base) e `obs: "atende-academia"`, e grava de volta. Campos que o sistema não mede (ex.: `ticket_medio`, `fat_cartao`) ficam como estavam. `indicadores` não entra. Sai com código 0.

## 15. LGPD

- `GET /api/alunos/{id}/dados` devolve tudo o que há do aluno: `aluno` `{id, nome, telefone, codigo, email, nascimento, consentimento_marketing, nao_contatar}`, `matriculas`, `reservas`, `checkins`, `avaliacoes` (com `resultado`), `ficha` (ou `null`) e `mensagens` = recebidas e enviadas, cada uma `{direcao: "entrada" | "saida", texto, quando}`.
- `DELETE /api/alunos/{id}`: nome vira `removido`; telefone, `codigo`, `email` e `nascimento` viram `null`; reservas `reservada` viram `cancelada` (vaga liberada, **sem** disparar lista de espera); avaliações `agendada` viram `cancelada`; `resultado` das avaliações vira `null`; ficha apagada; textos das mensagens dele viram `""`; pedidos de espera `pendente` são cancelados. Matrículas, check-ins e reservas `presente`/`falta` ficam (números agregados do `/api/raiox` continuam valendo). Depois disso, mensagens ao telefone antigo são tratadas como de telefone desconhecido e o `codigo` antigo dá 404 no check-in.
- Dados de avaliação física = sensíveis (seção 8). Nada de dado de aluno sai do sistema fora das integrações configuradas pelo próprio dono.

## 16. Fora do v1 (não implementar; portão humano ou próxima versão)

Cobrança, Pix, cartão, PSP, boleto e Pix Automático (só o status manual `pago/pendente`); catraca/leitor físico (o check-in é por código na recepção ou pelo chat); app do aluno; agendamento de avaliação pelo chat; aulas particulares/personal; horário por sala (a sala é só informativa); várias academias no mesmo servidor; login por usuário na página da equipe; WhatsApp Cloud API oficial da Meta (v1 usa a Evolution); SMS/e-mail; deploy na VPS (é do humano, README explica); LLM nas respostas (pode entrar depois atrás de uma opção desligada por padrão; os testes nunca a usam); geração automática dos SVGs por IA (os 12 são desenhados à mão); interface EN/ES.

## 17. Páginas

- `GET /` → HTML do chat do aluno, com elemento `id="chat"`, que usa `/api/mensagens`.
- `GET /equipe` → HTML da equipe com elementos `id="grade"`, `id="reservas"`, `id="checkins"`, `id="alunos"`, `id="planos"`, `id="fichas"`, `id="biblioteca"`, `id="fila-humano"` e `id="saida"`; pede o token e usa as rotas [R] (grade e reservas do dia, check-in por código, alunos e matrículas, planos, fichas, biblioteca, fila humana com responder/encerrar, caixa de saída, campanhas, Raio-X).
- `GET /exercicios/{id}` → seção 7.2.
- Páginas e seus recursos são servidos pelo próprio `./atende` (sem CDN, sem URL externa).

## 18. Cadastros [R]

| Método e rota | Corpo | Resposta |
|---|---|---|
| `GET /api/professores` | — | 200 `{"professores": [{id, nome, avaliacao, horarios, ativo}]}` ordem de cadastro |
| `POST /api/professores` | `{id, nome, avaliacao?, horarios?}` | 201; `id` repetido → 409 |
| `PUT /api/professores/{id}` | parcial | 200; inexistente → 404 |
| `DELETE /api/professores/{id}` | — | 200 `{"ativo": false}`. Inativo some de `/api/avaliacoes/horarios` e não aceita avaliação nova (422); aulas e avaliações já marcadas continuam |
| `POST /api/planos` / `PUT /api/planos/{id}` / `DELETE /api/planos/{id}` | `{id, nome, preco, vigencia_dias, aulas?}` / parcial / — | 201 (`id` repetido → 409) / 200 / 200 `{"ativo": false}` (some de `GET /api/planos` e do chat; matrículas existentes continuam) |
| `GET /api/grade` | — | 200 `{"grade": [{id, modalidade, professor, sala, dia, hora, duracao_min, vagas, ativo}]}` ordem de cadastro |
| `POST /api/grade` | `{id, modalidade, professor, sala, dia, hora, duracao_min, vagas}` | 201; `id` repetido → 409; modalidade/professor/sala inexistente → 422; `dia` fora de `seg..dom` → 400 |
| `PUT /api/grade/{id}` / `DELETE /api/grade/{id}` | parcial / — | 200 / 200 `{"ativo": false}` (as ocorrências somem de `/api/aulas` e do chat; reservas já feitas continuam com seus status) |
| `POST /api/exercicios` / `PUT` / `DELETE` | (seção 6.1) | |
| `GET /api/faq` / `POST /api/faq {perguntas, resposta}` / `DELETE /api/faq/{id}` | | 200 `{"faq": [{id, perguntas, resposta}]}` / 201 `{id}` (o bot usa na hora) / 204 (para de usar na hora) |
| `GET /api/modalidades` (público) / `POST /api/modalidades {id, nome}` / `GET /api/salas` / `POST /api/salas {id, nome}` | | 200 / 201 (`id` repetido → 409) |

## 19. Banco de dados

- `./atende backup --dados DIR --saida ARQ` → grava em `ARQ` uma cópia consistente de todo o estado (pode rodar com o servidor ligado). Código 0.
- `./atende restaurar --dados DIR --entrada ARQ` → com o servidor parado, substitui o estado de `DIR` pelo do backup. Código 0. Ao subir de novo, tudo volta como estava no momento do backup.

## 20. WhatsApp pela Evolution API

Variáveis: `EVOLUTION_URL` (ex.: endereço interno da Evolution, sem barra final), `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCIA`, `WEBHOOK_SEGREDO`. Sem `EVOLUTION_URL` → canal simulado (só caixa de saída, `status: "simulado"`). `.env.exemplo` e o código não contêm nenhuma URL (nem em comentário).

**Entrada** — `POST /webhook/evolution/{WEBHOOK_SEGREDO}` (segredo errado → 404). Formato da Evolution v2:
```json
{"event": "messages.upsert", "instance": "academia",
 "data": {"key": {"remoteJid": "5541999990001@s.whatsapp.net", "fromMe": false, "id": "ABC123"},
          "pushName": "Maria", "message": {"conversation": "oi"}, "messageType": "conversation"}}
```
- Sempre responde 200. Ignora: `event` diferente de `messages.upsert`, `fromMe: true`, `remoteJid` de grupo (`@g.us`), `key.id` já processado (a Evolution reenvia).
- Texto = `message.conversation` ou `message.extendedTextMessage.text`. Sem texto (áudio, imagem...) → responde `Por enquanto só consigo ler mensagens de texto.`
- Telefone = dígitos do `remoteJid` antes do `@`, normalizado como na seção 3. Passa pela mesma conversa da seção 11 (o mesmo aluno, o mesmo estado).
- Cada resposta da conversa vai por `POST {EVOLUTION_URL}/message/sendText/{EVOLUTION_INSTANCIA}` com header `apikey: {EVOLUTION_API_KEY}` e corpo `{"number": "<dígitos com 55>", "text": "<texto>"}`, na ordem — exceto a explicação de exercício com MP4, que vai por `sendMedia` (seção 7.3).

**Saída** (vencimento, reativação, espera, aula cancelada, avaliação, campanha, humano): com a Evolution configurada, cada mensagem da caixa de saída é enviada do mesmo jeito (`sendText`). Em `/api/saida` cada mensagem tem `status`: `enviado` (2xx), `pendente` (erro HTTP ou de conexão) ou `simulado`. `POST /api/tarefas/rodar` reenvia as `pendente` e devolve `"reenviadas": n` (as que viraram `enviado`). `tarefas/rodar`, `responder`, `campanhas`, `cancelar` (reserva e ocorrência) só devolvem a resposta HTTP depois de tentar os envios (o `status` já está definido). Respostas ao webhook e avisos ao Telegram podem ser assíncronos.

## 21. Atendimento interno pelo Telegram

Variáveis: `TELEGRAM_API_URL` (endereço da API, sem barra final), `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` (grupo da equipe), `TELEGRAM_SEGREDO`. Sem elas, nada vai ao Telegram (o resto funciona igual). Envio: `POST {TELEGRAM_API_URL}/bot{TELEGRAM_TOKEN}/sendMessage` com `{"chat_id", "text"[, "reply_to_message_id"]}`; a resposta do Telegram traz `result.message_id`.

**Atendimento humano** (`/api/atendimento-humano`, só os `aberto`):
- Ao abrir (pedido de atendente, alerta de saúde, 2º "não entendi"): manda ao grupo um texto com `#<id>`, telefone, nome (se houver), motivo, a última mensagem do aluno e, se `prioridade` for `alta`, a palavra `ALTA`. Guarda o `message_id`.
- Enquanto o atendimento do telefone estiver `aberto`, o bot **não responde** sozinho (`respostas: []`), exceto alerta de saúde (regra 1); cada mensagem do aluno vai ao grupo como `#<id> <nome ou telefone>: <texto>`, em resposta (`reply_to_message_id`) à mensagem de abertura.
- `POST /webhook/telegram` exige header `X-Telegram-Bot-Api-Secret-Token: {TELEGRAM_SEGREDO}` (senão 401). Só aceita updates de `message.chat.id == TELEGRAM_CHAT_ID` (comparados como texto); os outros são ignorados (200, sem efeito).
- Mensagem da equipe que é resposta (`reply_to_message.message_id`) a uma mensagem do atendimento `#id` → o texto vai ao aluno (caixa de saída `tipo: "humano"`, e pela Evolution se configurada).
- Comandos: `/responder <id> <texto>` (o mesmo, sem precisar responder em cima); `/encerrar <id>` → status `encerrado`, o bot volta a responder aquele telefone; `/fila` → o bot manda a lista dos abertos (cada um com `#id`); `/aulas [AAAA-MM-DD]` (padrão: hoje pelo relógio) → manda as ocorrências não canceladas do dia, uma linha `HH:MM <modalidade> (<professor>) — <reservadas>/<vagas>` cada, em ordem de `inicio`; dia sem aula → texto contém `sem aulas`.
- Pela página da equipe [R]: `POST /api/atendimento-humano/{id}/responder {texto}` e `POST /api/atendimento-humano/{id}/encerrar` fazem o mesmo.
- **Avisos à equipe:** reserva feita pelo chat → `Nova reserva: DD/MM HH:MM <nome> — <modalidade>`; cancelamento de reserva pelo chat → texto começando com `Cancelada:` e com `DD/MM HH:MM`.

## 22. Docker / VPS

- `Dockerfile` (imagem oficial `python:3-slim` ou similar, **sem `pip install`**) que roda `./atende serve --host 0.0.0.0 --porta 8080 --dados /dados`, com `HEALTHCHECK` em `/api/saude` (via `python3 -c`, sem `curl`). O container sobe mesmo sem volume em `/dados` (seção 1: o diretório é criado e `academia.json` copiado do exemplo). A imagem leva `web/` (inclusive os SVGs) copiado **explicitamente** (uma linha `COPY web/ ./web/`, não só `COPY . .`); os MP4 são opcionais (`EXERCICIOS_MP4_DIR` pode apontar para o volume).
- `docker-compose.yml` com o serviço `atende`: `build: .`, `restart: unless-stopped`, `env_file: .env`, volume para `/dados`, porta publicada só em `127.0.0.1:8080` (na VPS fica atrás de proxy reverso com HTTPS).
- `.env.exemplo` com todas as variáveis das seções 1, 20 e 21 (`PUBLIC_URL`, `EXERCICIOS_MP4_DIR`, `EVOLUTION_*`, `WEBHOOK_SEGREDO`, `TELEGRAM_*`), **todas vazias**, nenhum segredo real e **nenhuma URL** (a palavra `http` não aparece no arquivo, nem em comentário).
- `README.md` com a seção **Deploy na VPS**: subir o compose, proxy HTTPS, `PUBLIC_URL`, configurar o webhook da Evolution para `/webhook/evolution/<segredo>` (evento `MESSAGES_UPSERT`), registrar o webhook do Telegram com `setWebhook` + `secret_token`, gerar os MP4 (`tools/render-exercicios`) e o backup diário (`./atende backup` no cron) — **sem remover** a seção "Como rodar no seu ambiente".
