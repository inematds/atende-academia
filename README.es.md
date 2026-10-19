# atende-academia

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Atende Academia](guia/assets/banner.jpg)](https://inematds.github.io/atende-academia/guia/)

## 📖 Guía de uso

Landing y guía paso a paso (PT/EN/ES): **https://inematds.github.io/atende-academia/guia/** · [English](https://inematds.github.io/atende-academia/guia/en/) · [Español](https://inematds.github.io/atende-academia/guia/es/)

Atención al alumno de un gimnasio o estudio pequeño, en Python 3 solo con biblioteca estándar (HTTP + SQLite): alumnos y planes, clases colectivas con reserva y lista de espera, check-in y reactivación, ficha de entrenamiento, **explicación animada de ejercicios**, evaluación física, conversación por chat web y WhatsApp (Evolution API), equipo por Telegram, LGPD y exportación al Panel de Recuperación del Raio-X de Margem.

**Estado (19/10/2026): v0.11.0 — implementación completa; 99/99 pruebas, `LIMITES OK`. Telegram, páginas `/` y `/equipe`, Docker y `tools/render-exercicios` entregados.** Ver "Cómo ejecutarlo en tu entorno".

## Qué hace el sistema (v1)

- **Alumnos y planes:** registro con código de check-in; planes mensual/trimestral/anual/clases sueltas con precio y vigencia; matrícula con estado `ativa`, `vencida`, `trancada`, `cancelada`; cobro solo como **estado manual** (`pago`/`pendente`) y aviso de vencimiento.
- **Clases colectivas:** grilla semanal (modalidad, profesor, sala, cupos); reserva con límite de cupos y anticipación; cancelación con plazo; lista de espera con oferta automática; falta automática (reserva sin check-in); último cupo disputado → un 201, el resto 409.
- **Check-in y frecuencia:** por código en la recepción o por el chat ("llegué"); el alumno sin check-in hace N días recibe reactivación (solo con consentimiento); frecuencia y números del mes para el Raio-X.
- **Entrenamiento:** el profesor arma la ficha con ejercicios de la biblioteca (series, repeticiones, carga, descanso); el alumno pide "mi entrenamiento de hoy"; cualquier ejercicio del catálogo tiene **animación SVG** (`/exercicios/<id>`) y, en WhatsApp, MP4 generado por HyperFrames cuando exista.
- **Evaluación física** agendada con el profesor; el resultado es un dato sensible (solo equipo, nunca por la conversación).
- **Conversación:** clases, reservar/cancelar, mi plan, mi entrenamiento, explicar ejercicio, FAQ, atención humana, alerta de salud (192), "PARAR".
- **Equipo:** página `/equipe` con token y Telegram (`/aulas [fecha]`, `/fila`, `/responder`, `/encerrar`, avisos de reserva y cancelación).
- **Campañas** solo con consentimiento y límite mínimo de publicidad; **LGPD** (exportar, anonimizar); **backup/restauración**; **Docker** para VPS.

Contrato completo: `docs/ESPECIFICACAO.md` (22 secciones). Fuera de la v1: sección 16.

## Cómo ejecutarlo en tu entorno

El sistema está **implementado**: v0.11.0, 99/99 pruebas, `LIMITES OK` y verificación independiente aprobada. Cualquier persona puede ejecutarlo en su propio entorno.

### Requisitos previos

- Linux/macOS con `git` y `python3` ≥ 3.10. La aplicación no tiene dependencias; `pytest` (`pip install pytest`) solo sirve para comprobar las pruebas.
- Para el despliegue: `docker` (con `docker compose`).
- Opcional, para los MP4 de los ejercicios: Node 22 + HyperFrames + `ffprobe`. El `tools/render-exercicios` y el verificador solo usan el HyperFrames ya instalado (`npx --no-install hyperframes`); para instalarlo una vez: `npm install hyperframes` en la raíz del repo (`node_modules/`, `package.json` y `package-lock.json` están en el `.gitignore`, así que el `verificar-limites.sh` no los ve) o `npm install -g hyperframes`.

### 1. Clonar y comprobar

```sh
git clone https://github.com/inematds/atende-academia && cd atende-academia
python3 -m pytest -q tests/ | tail -n 1                          # 99 passed
bash longrun/2026-10-05-academia-v1/verificar-limites.sh          # LIMITES OK al cierre; hoy marca solo guia/ y README.en/es (docs posteriores)
```

`LIMITES OK` = hash del contrato intacto, nº de pruebas igual, solo archivos del alcance, sin dependencia externa, sin URL externa en el código, sin clave, sin `0.0.0.0` en el código, ningún MP4/`node_modules` commiteado.

### 2. Ejecutar

```sh
mkdir -p dados && cp exemplos/academia.json dados/academia.json   # edita nombre, token, grilla, planes
./atende serve --porta 8080 --dados dados
./atende raiox --dados dados --mes 2026-10 --acompanhamento acompanhamento.json
./atende backup --dados dados --saida backups/academia.zip
```

Chat del alumno en `/`, equipo en `/equipe` (token de `academia.json` en el header `X-Token`), animación de cada ejercicio en `/exercicios/<id>`. `PUBLIC_URL` (dirección pública, HTTPS, sin barra final) entra en los enlaces enviados al alumno; sin ella los enlaces son relativos. Sin las variables de Evolution y de Telegram, la bandeja de salida es simulada y no sale ninguna llamada de red. Las 20 decisiones por defecto están en `docs/DECISOES-ABERTAS.md`.

**MP4 de los ejercicios (WhatsApp no muestra SVG):** `tools/render-exercicios [--ids a,b] [--saida DIR]` genera `web/exercicios/<id>.mp4` (720×720, 4 s en bucle, sin audio) a partir de cada SVG con HyperFrames — render local por Chromium, sin API ni cuenta. Necesita Node 22+, HyperFrames instalado (`npm install hyperframes` en la raíz; el script no descarga nada por sí solo) y `ffprobe`. La composición es **solo CSS** (el SVG inline dentro de `data-width="720" data-height="720" data-duration="4"`, sin GSAP ni CDN): el render busca cada cuadro por los adaptadores CSS/WAAPI, por eso los SVG usan `@keyframes` con duraciones de 1, 2 o 4 s y nunca SMIL. Es un paso de build: se ejecuta una vez en la máquina de quien publica, no en el servidor ni en las pruebas. **Este render aún no se ha ejecutado** (las animaciones SVG funcionan en la web). Con el MP4 presente y `PUBLIC_URL` definida, el bot envía el video por `sendMedia`; si no, manda el enlace de la página.

### 3. Verificación independiente (nivel 4)

```sh
python3 longrun/2026-10-05-academia-v1/verificar-independente.py   # INDEPENDENTE OK
```

Busca valores del fixture copiados en el código; levanta un gimnasio **nunca visto** (otra grilla, planes, plazos, feriado, reloj) y comprueba reglas que solo pasan si la lógica es general; abre 3 SVG en un Chromium headless y exige que dos cuadros en instantes distintos sean diferentes (prueba de movimiento; sin Chromium que pase la calibración → `PULADO`); si HyperFrames está instalado, renderiza un ejercicio con `tools/render-exercicios` y comprueba 720×720, ~4 s, sin audio con `ffprobe` (si no → `PULADO`); hace `docker build` y prueba el healthcheck del contenedor (sin `docker` → `PULADO`). En la entrega salió `INDEPENDENTE OK (movimento: chromium, hyperframes: pulado, docker: ok)`. Después abre `/`, `/equipe` y `/exercicios/prancha` en el navegador.

### 4. Cómo se construyó (para rehacer o adaptar)

El sistema fue construido con el método de ejecución larga (`~/projetos/execucao-longa`: `tools/loop-longrun.sh`, `docs/PLANO-EXECUCAO-LONGA.md`), por un agente mediante la **suscripción** (Codex CLI y Claude Code, ninguna API llamada):

1. Las decisiones de `docs/DECISOES-ABERTAS.md` fueron respondidas y el contrato fue congelado con `bash longrun/2026-10-05-academia-v1/congelar.sh` (graba `hash-congelado.txt`). Contrato, pruebas y los dos verificadores quedaron protegidos: el agente no los alteraba; una prueba en conflicto con la spec iba a `failures.md` (compuerta humana).
2. El agente trabajó en bucle headless (`~/projetos/execucao-longa/tools/loop-longrun.sh longrun/2026-10-05-academia-v1`, Codex `gpt-6-astra`, configuración en `loop.env`: 20 ciclos × 30 min, 8 GB, parada tras 3 ciclos sin avance, `flock`, `timeout`, `MemoryMax`, reversión de ciclo que tocara un archivo protegido, checkpoint por ciclo) y fue concluido por Claude Code, hasta **99 passed** y **LIMITES OK**.
3. El seguimiento quedó en `longrun/2026-10-05-academia-v1/` (`loop.log`, `state.md`, `progress.md`).

¿Quieres cambiar una regla marcada ⚠ o llevar el molde a otro negocio? Edita `docs/ESPECIFICACAO.md` y las pruebas, congela de nuevo y ejecuta el bucle headless, o el `/goal` en el Codex TUI (`codex -c sandbox_workspace_write.network_access=true` + `longrun/2026-10-05-academia-v1/prompt-goal-codex.md`) o en Claude Code (`longrun/2026-10-05-academia-v1/prompt-goal-claude.md`).

## Despliegue en la VPS

Paso del dueño, con sus credenciales y su máquina (el sistema nunca hace esto solo).

1. **Levantar el compose.** En la VPS, con Docker: clona el repo, `cp .env.exemplo .env`, rellena las variables y ejecuta `docker compose up -d --build`. El servicio `atende` escucha solo en `127.0.0.1:8080`, guarda todo en `./dados` (volumen `/dados`) y tiene healthcheck en `/api/saude`. En el primer arranque, `dados/academia.json` se copia del ejemplo: edita nombre, **token**, grilla y planes y reinicia (`docker compose restart`).
2. **Proxy HTTPS.** Coloca un proxy inverso (Caddy, Nginx o Traefik) con certificado delante de `127.0.0.1:8080`, en el dominio del gimnasio. Nunca publiques el puerto 8080 directamente.
3. **`PUBLIC_URL`.** En el `.env`, `PUBLIC_URL` = la dirección HTTPS del dominio, sin barra final. Es lo que entra en los enlaces de ejercicio y en el `sendMedia` del MP4.
4. **Webhook de Evolution.** Rellena `EVOLUTION_URL` (dirección interna de Evolution), `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCIA` y un `WEBHOOK_SEGREDO` largo y aleatorio. En el panel de Evolution, apunta el webhook de la instancia a `<PUBLIC_URL>/webhook/evolution/<WEBHOOK_SEGREDO>` con el evento `MESSAGES_UPSERT`. Secreto incorrecto responde 404.
5. **Webhook de Telegram.** Crea el bot en BotFather, colócalo en el grupo del equipo y rellena `TELEGRAM_API_URL` (dirección de la API de Telegram), `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` (id del grupo) y `TELEGRAM_SEGREDO`. Registra el webhook llamando a `setWebhook` de la API del bot con `url=<PUBLIC_URL>/webhook/telegram` y `secret_token=<TELEGRAM_SEGREDO>` — el sistema rechaza (401) el update sin ese encabezado e ignora otros chats. En el grupo: responder sobre el mensaje `#id`, `/responder <id> <texto>`, `/encerrar <id>`, `/fila`, `/aulas [AAAA-MM-DD]`.
6. **Generar los MP4.** En una máquina con Node 22+, `npm install hyperframes` y `ffprobe`, ejecuta `tools/render-exercicios` (o `--ids prancha,agachamento --saida DIR`) y copia los `.mp4` a la carpeta indicada por `EXERCICIOS_MP4_DIR` (p. ej.: `/dados/mp4` dentro del contenedor = `./dados/mp4` en la VPS). Sin MP4, WhatsApp recibe el enlace de la página animada.
7. **Backup diario.** En el cron del host, por ejemplo a las 3 h: `docker compose exec -T atende ./atende backup --dados /dados --saida /dados/backups/academia-$(date +\%F).zip` (el `./atende backup` puede ejecutarse con el servidor encendido). Para restaurar: detén el servicio, ejecuta `./atende restaurar --dados /dados --entrada <archivo>` y levántalo de nuevo. Guarda copias fuera de la VPS.

## Archivos

- `docs/ESPECIFICACAO.md` — contrato (22 secciones, tabla de rutas, reglas con fronteras, fuera de la v1).
- `docs/DECISOES-ABERTAS.md` — decisiones con propuesta por defecto; preguntas para el dueño.
- `docs/MAPA-RAIO-X.md` — cada fuga del paquete `servicos` → pieza de la v1 o motivo de quedar fuera.
- `tests/` — 99 pruebas caja negra (`conftest.py` levanta el CLI, reloj fijo, servidor falso de Evolution/Telegram, carpeta temporal de MP4). Fixture en `tests/fixtures/academia.json`; copia en `exemplos/`.
- `longrun/2026-10-05-academia-v1/` — goal (nivel 3+), plan, state, loop.env, prompts, `congelar.sh`, `verificar-limites.sh`, `verificar-independente.py`.
- `FALHAS.md` — una línea por falla (fecha, qué se rompió, menor corrección, prompt | infra).
