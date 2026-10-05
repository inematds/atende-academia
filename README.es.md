# atende-academia

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Atende Academia](guia/assets/banner-es.jpg)](https://inematds.github.io/atende-academia/guia/es/)

## 📖 Guía de uso

Landing y guía paso a paso: **https://inematds.github.io/atende-academia/guia/es/** · [Português](https://inematds.github.io/atende-academia/guia/) · [English](https://inematds.github.io/atende-academia/guia/en/)

Atención al alumno de un gimnasio o estudio pequeño, en Python 3 solo con la biblioteca estándar (HTTP + SQLite): alumnos y planes, clases grupales con reserva y lista de espera, check-in y reactivación, rutina de entrenamiento, **explicación animada de ejercicios**, evaluación física, conversación por chat web y WhatsApp (Evolution API), equipo por Telegram, LGPD y exportación al Panel de Recuperación de Raio-X de Margem. El chat y los datos están en portugués en la v1; la LGPD (la ley brasileña de protección de datos) y el `192` (el número de la ambulancia en Brasil) son de Brasil.

**Estado (05/10/2026): planificado: contrato, 99 pruebas y carpeta de ejecución larga listos; implementación pendiente.** Ver "Cómo ejecutarlo en tu entorno".

## Qué hace el sistema (v1)

- **Alumnos y planes:** alta con código de check-in; planes mensual/trimestral/anual/clases sueltas con precio y vigencia; matrícula con estado `ativa`, `vencida`, `trancada`, `cancelada` (activa, vencida, congelada, cancelada); cobro solo como **estado manual** (`pago`/`pendente`, pagado o pendiente) y aviso de vencimiento.
- **Clases grupales:** grilla semanal (modalidad, profesor, sala, cupos); reserva con límite de cupos y anticipación; cancelación con plazo; lista de espera con oferta automática; falta automática (reserva sin check-in); último cupo disputado → un 201, el resto 409.
- **Check-in y frecuencia:** por código en la recepción o por el chat ("cheguei", "llegué"); al alumno sin check-in hace N días le llega una reactivación (solo con consentimiento); frecuencia y números del mes para Raio-X.
- **Entrenamiento:** el profesor arma la rutina con ejercicios de la biblioteca (series, repeticiones, carga, descanso); el alumno pide "meu treino de hoje" (mi entrenamiento de hoy); cualquier ejercicio del catálogo tiene **animación SVG** (`/exercicios/<id>`) y, en WhatsApp, un MP4 generado por HyperFrames cuando exista.
- **Evaluación física** agendada con el profesor; el resultado es un dato sensible (solo el equipo, nunca por la conversación).
- **Conversación:** clases, reservar/cancelar, mi plan, mi entrenamiento, explicar un ejercicio, FAQ, agente humano, alerta de salud (192), "PARAR".
- **Equipo:** página `/equipe` con token y Telegram (`/aulas [fecha]`, `/fila`, `/responder`, `/encerrar`, avisos de reserva y cancelación).
- **Campañas** solo con consentimiento y una salvaguarda mínima de publicidad; **LGPD** (exportar, anonimizar); **respaldo/restauración**; **Docker** para un VPS.

Contrato completo: `docs/ESPECIFICACAO.md` (22 secciones). Fuera de la v1: sección 16.

## Cómo ejecutarlo en tu entorno

El proyecto está **planificado, no implementado**: contrato y pruebas congelados, un agente implementa hasta que pasen las 99 pruebas. Cualquier persona puede ejecutarlo en su propio entorno.

### Requisitos

- Linux/macOS con `git`, `python3` ≥ 3.10 y `pytest` (`pip install pytest`; es una herramienta de desarrollo, la aplicación no depende de ella).
- Un agente por **suscripción**: Codex CLI (`codex`) o Claude Code (`claude`). No se llama a ninguna API.
- Para la verificación independiente final: `docker`; opcionalmente un Chromium (Playwright o un binario) para la prueba de movimiento de los SVG y Node 22 + HyperFrames + `ffprobe` para comprobar el MP4. Sin ellos el verificador imprime `PULADO` (omitido) para esa etapa (nunca un "ok" silencioso). El verificador y `tools/render-exercicios` solo usan el HyperFrames ya instalado (`npx --no-install hyperframes`); para instalarlo una vez: `npm install hyperframes` en la raíz del repo (`node_modules/`, `package.json` y `package-lock.json` están en el `.gitignore`, así que `verificar-limites.sh` no los ve) o `npm install -g hyperframes`. Instálalo **después** de que el loop termine (antes de la verificación independiente): el agente no lo necesita y no debe descargar paquetes.
- Método y herramientas de ejecución larga: un clon de `~/projetos/execucao-longa` (`tools/loop-longrun.sh`, `docs/PLANO-EXECUCAO-LONGA.md`). Si no lo tienes, la ruta interactiva `/goal` (abajo) no lo necesita.

### 1. Responder las decisiones y congelar el contrato

```sh
cd atende-academia
# lee docs/DECISOES-ABERTAS.md; "ok en todo" = nada que cambiar
python3 -m pytest -q --collect-only | tail -n 1     # 99 tests collected
bash longrun/2026-10-05-academia-v1/congelar.sh     # guarda hash-congelado.txt y hace 1 commit
```

Si cambias algo marcado con ⚠ en las decisiones, edita `docs/ESPECIFICACAO.md` y las pruebas **antes** de congelar. Una vez congelado, el contrato, las pruebas y los dos verificadores quedan protegidos: el agente no los altera; si una prueba contradice la spec, lo registra en `failures.md` y se detiene (compuerta humana).

### 2a. Loop headless (Codex `gpt-6-astra`)

```sh
~/projetos/execucao-longa/tools/loop-longrun.sh longrun/2026-10-05-academia-v1
```

Configuración en `longrun/2026-10-05-academia-v1/loop.env` (prueba rápida/final, archivos protegidos, 20 ciclos × 30 min, 8 GB, parada tras 3 ciclos sin avance, `CODEX_ARGS` que libera un socket local en el sandbox). El loop hace `flock`, `timeout`, `MemoryMax`, revierte un ciclo que toque un archivo protegido, hace commit de un checkpoint por ciclo y se detiene solo cuando pasa la prueba final.

### 2b. `/goal` en el Codex TUI

```sh
cd atende-academia && codex -c sandbox_workspace_write.network_access=true
```

Pega todo `longrun/2026-10-05-academia-v1/prompt-goal-codex.md` (empieza con `/goal`). Sigue con `/goals`; `/goal pause|resume`.

### 2c. `/goal` en Claude Code

Una sesión **nueva** de Claude Code abierta en la carpeta del proyecto; sigue `longrun/2026-10-05-academia-v1/prompt-goal-claude.md` (la condición de `/goal` + el bloque de `prompt-goal-codex.md` como primer mensaje).

### 3. Hacer el seguimiento

```sh
tail -n 20 longrun/2026-10-05-academia-v1/loop.log        # headless
cat longrun/2026-10-05-academia-v1/state.md               # Funciona / Falta / Cómo retomar
tail -n 5 longrun/2026-10-05-academia-v1/progress.md
python3 -m pytest -q tests/ | tail -n 3
```

Listo = `python3 -m pytest -q tests/` → **99 passed** y `bash longrun/2026-10-05-academia-v1/verificar-limites.sh` → **LIMITES OK** (hash del contrato intacto, mismo número de pruebas, solo archivos del alcance, sin dependencia externa, sin URL externa en el código, sin clave, sin `0.0.0.0` en el código, ningún MP4 ni `node_modules` en el commit).

### 4. Verificación independiente (nivel 4, humana)

```sh
python3 longrun/2026-10-05-academia-v1/verificar-independente.py   # INDEPENDENTE OK
```

Busca valores del fixture copiados en el código; levanta un gimnasio **nunca visto** (otra grilla, planes, plazos, feriado, reloj) y comprueba reglas que solo pasan si la lógica es general; abre 3 SVG en un Chromium headless y exige que dos cuadros en instantes distintos sean diferentes (prueba de movimiento; sin un Chromium que pase la calibración → `PULADO`); si HyperFrames está instalado, renderiza un ejercicio con `tools/render-exercicios` y comprueba 720×720, ~4 s, sin audio con `ffprobe` (si no → `PULADO`); hace `docker build` y prueba el healthcheck del contenedor (sin `docker` → `PULADO`). La última línea dice `INDEPENDENTE OK (movimento: ..., hyperframes: ..., docker: ...)` para que veas qué se comprobó de verdad. Después abre `/`, `/equipe` y `/exercicios/prancha` en el navegador.

## Ejecutar (una vez implementado)

```sh
mkdir -p dados && cp exemplos/academia.json dados/academia.json   # edita nombre, token, grilla, planes
./atende serve --porta 8080 --dados dados
./atende raiox --dados dados --mes 2026-10 --acompanhamento acompanhamento.json
./atende backup --dados dados --saida backups/academia.zip
```

Chat del alumno en `/`, equipo en `/equipe` (token de `academia.json` en el header `X-Token`), animación de cada ejercicio en `/exercicios/<id>`. `PUBLIC_URL` (dirección pública, HTTPS, sin barra final) entra en los enlaces enviados al alumno; sin ella los enlaces son relativos.

**MP4 de los ejercicios (WhatsApp no muestra SVG):** `tools/render-exercicios [--ids a,b] [--saida DIR]` genera `web/exercicios/<id>.mp4` (720×720, loop de 4 s, sin audio) a partir de cada SVG con HyperFrames: render local por Chromium, sin API ni cuenta. Necesita Node 22+, HyperFrames instalado (`npm install hyperframes` en la raíz; el script no descarga nada por sí solo) y `ffprobe`. La composición es **solo CSS** (el SVG en línea dentro de `data-width="720" data-height="720" data-duration="4"`, sin GSAP ni CDN): el render busca cada cuadro por los adaptadores CSS/WAAPI, por eso los SVG usan `@keyframes` con duraciones de 1, 2 o 4 s y nunca SMIL. Es un paso de build: se ejecuta una vez en la máquina de quien publica, no en el servidor ni en las pruebas. Con el MP4 presente y `PUBLIC_URL` definida, el bot envía el video por `sendMedia`; si no, manda el enlace de la página.

## Archivos

- `docs/ESPECIFICACAO.md`: el contrato (22 secciones, tabla de rutas, reglas con límites, fuera de la v1).
- `docs/DECISOES-ABERTAS.md`: decisiones con propuesta por defecto; preguntas para el dueño.
- `docs/MAPA-RAIO-X.md`: cada fuga del paquete `servicos` → una pieza de la v1 o el motivo de quedar fuera.
- `tests/`: 99 pruebas de caja negra (`conftest.py` levanta el CLI, un reloj fijo, un servidor falso de Evolution/Telegram, una carpeta temporal de MP4). Fixture en `tests/fixtures/academia.json`; copia en `exemplos/`.
- `longrun/2026-10-05-academia-v1/`: goal (nivel 3+), plan, state, loop.env, prompts, `congelar.sh`, `verificar-limites.sh`, `verificar-independente.py`.
- `FALHAS.md`: una línea por falla (fecha, qué se rompió, corrección mínima, prompt | infra).
