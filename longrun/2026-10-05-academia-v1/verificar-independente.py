#!/usr/bin/env python3
"""Verificação independente (nível 4) — rodar DEPOIS que o loop disser concluído. O agente não vê este arquivo no prompt.

1. Procura valores do fixture copiados no código (atalho para passar nos testes).
2. Sobe o sistema com uma academia NUNCA vista (outra grade, planos de 15 e 45 dias, pacote de 3 aulas, passo de 20 min,
   antecedência de 3 dias, cancelamento 24 h, inatividade 10 dias, aviso 3 dias, feriado novo, relógio em novembro)
   e confere regras que só passam se a lógica for geral. Tudo explícito: nenhum atalho do conftest com padrão do fixture.
3. Prova de movimento: 3 SVGs do repo num Chromium headless (Playwright, ou binário do Chromium) em 3 instantes;
   os quadros têm de diferir. Cada candidato a navegador é CALIBRADO antes (SVG estático gravado + SVG CSS animado
   conhecido com quadros diferentes); nenhum calibra → "PULADO" (nunca "OK", nunca falha falsa).
4. HyperFrames: se `npx --no-install hyperframes` responde, renderiza 1 exercício com tools/render-exercicios e confere
   720×720, 3,5–4,5 s, sem áudio com ffprobe. Senão → "PULADO".
5. docker build + healthcheck do container; sem docker → "PULADO".
Ferramenta ausente nunca vira traceback nem "ok": vira linha "PULADO: ..." e entra na última linha.
Saída: INDEPENDENTE OK (movimento: ..., hyperframes: ..., docker: ...), ou a lista do que falhou.

Armadilhas medidas em 05/10/2026 nesta máquina (spark-922b, arm64): o chromium do snap NÃO grava em /tmp (tmp privado)
→ os quadros vão numa pasta temporária DENTRO do repo (`.verif-svg-*`, no .gitignore); o chrome do Playwright fica em
`~/.cache/ms-playwright/chromium-*/chrome-linux-arm64/chrome` (glob `chrome-linux*`); animação CSS de `transform` só segue
`--virtual-time-budget` com `--disable-threaded-animation` (sem a flag, quadros iguais). SMIL não entra (seção 7.1: só CSS).
"""
import glob
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

RAIZ = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "tests"))
from conftest import Servidor  # noqa: E402

falhas = []


def confere(cond, msg):
    if not cond:
        falhas.append(msg)


# ---------------------------------------------------------------------------------------------
# 3. prova de movimento (usada também pelos testes do próprio verificador)
INSTANTES_MS = (250, 1150, 2450)   # diferenças 900, 1300, 2200 ms: nenhum período ≥ 0,2 s as divide todas


PROVA_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10" width="10" height="10">'
             '<rect width="10" height="10" fill="#fff"/></svg>')
# SVG CSS animado conhecido (mesmo molde da seção 7.1): calibra o navegador — tem de dar quadros diferentes
PROVA_ANIMADA = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="400" height="400"><title>Prova</title>'
                 '<style>.q{transform-origin:200px 300px;animation:sobe 2s ease-in-out infinite}'
                 '@keyframes sobe{0%,100%{transform:translateY(0)}50%{transform:translateY(-120px)}}</style>'
                 '<rect width="400" height="400" fill="#fff"/><g class="q"><circle cx="200" cy="300" r="40" fill="#222"/></g></svg>')


def _screenshot_chromium(chrome, svg, ms, png):
    # --disable-threaded-animation: animação CSS de transform roda no compositor e NÃO segue o tempo virtual
    # (quadro quase aleatório); na thread principal ela acompanha --virtual-time-budget.
    subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--disable-threaded-animation",
                    "--hide-scrollbars", "--window-size=400,400", f"--virtual-time-budget={ms}",
                    f"--screenshot={png}", svg.resolve().as_uri()], capture_output=True, timeout=120)
    return png.read_bytes() if png.exists() else b""


def _mexe(quadros):
    return bool(quadros) and all(quadros) and len(set(quadros)) > 1


def _navegador(pasta):
    """Devolve ("playwright", None), ("chromium", caminho) ou (None, None). `pasta` fica DENTRO do repo (o chromium do
    snap não enxerga /tmp e devolveria PNG vazio = falha falsa). Cada candidato é CALIBRADO antes de valer: grava um SVG
    estático e mostra quadros diferentes num SVG CSS animado conhecido; quem não calibra é descartado (nunca "não se mexe"
    por culpa do navegador). Nenhum candidato → (None, None) → PULADO."""
    animado = pasta / "prova-anim.svg"
    animado.write_text(PROVA_ANIMADA)
    try:
        import playwright.sync_api  # noqa: F401
        if _mexe(_quadros_playwright(animado)):
            return "playwright", None
    except Exception:
        pass
    estatico = pasta / "prova.svg"
    estatico.write_text(PROVA_SVG)
    # chrome completo do Playwright (chrome-linux ou chrome-linux-arm64); o chrome-headless-shell fica de fora
    cands = sorted(glob.glob(os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome")), reverse=True)
    cands += [p for p in (shutil.which(n) for n in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome")) if p]
    for chrome in cands:
        try:
            if not _screenshot_chromium(chrome, estatico, 100, pasta / "prova.png"):
                continue
            if _mexe(_quadros_chromium(chrome, animado, pasta)):
                return "chromium", chrome
        except Exception:
            continue
    return None, None


def _quadros_chromium(chrome, svg, pasta):
    return [_screenshot_chromium(chrome, svg, ms, pasta / f"{svg.stem}-{ms}.png") for ms in INSTANTES_MS]


def _quadros_playwright(svg):
    from playwright.sync_api import sync_playwright
    quadros = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 400, "height": 400})
        pg.goto(svg.resolve().as_uri())
        t0 = 0
        for ms in INSTANTES_MS:
            pg.wait_for_timeout(ms - t0)
            t0 = ms
            quadros.append(pg.screenshot())
        b.close()
    return quadros


def prova_movimento(svgs, pasta):
    """Para cada SVG: True se ao menos dois dos três quadros diferem. Devolve (via, {svg: bool})."""
    via, chrome = _navegador(pasta)
    if via is None:
        return None, {}
    res = {}
    for svg in svgs:
        try:
            q = _quadros_playwright(svg) if via == "playwright" else _quadros_chromium(chrome, svg, pasta)
        except Exception:
            q = []
        res[svg.name] = _mexe(q)
    return via, res


class _Pular(Exception):
    pass


def main():
    # 1. valores fixos do fixture no código
    alvo = [p for p in ("atende", "src", "web", "tools") if (RAIZ / p).exists()]
    for trecho in ("Movimento Teste", "segredo-teste", "Rua das Palmeiras", "41999990001", "2026-10-06",
                   "pil-qua-9", "spin-ter-7", "Água Verde"):
        r = subprocess.run(["grep", "-rnF", trecho, *alvo], cwd=RAIZ, capture_output=True, text=True)
        confere(r.stdout == "", f"valor do fixture no código: {trecho!r}")

    # 2. academia nunca vista — agora = ter 03/11/2026 06:00; feriado qui 19/11
    vazio = {d: [] for d in ("seg", "ter", "qua", "qui", "sex", "sab", "dom")}
    cfg = {
        "nome": "Studio Corpo Livre", "token": "outro-token-xyz", "passo_min": 20, "avaliacao_duracao_min": 40,
        "avaliacao_antecedencia_horas": 1, "avaliacao_lembrete_horas": 48, "reserva_antecedencia_dias": 3,
        "cancelamento_prazo_horas": 24, "inatividade_dias": 10, "vencimento_aviso_dias": 3, "feriados": ["2026-11-19"],
        "horarios": dict(vazio, **{d: [["07:00", "21:00"]] for d in ("seg", "ter", "qua", "qui", "sex")}),
        "modalidades": [{"id": "yoga", "nome": "Yoga"}, {"id": "cross", "nome": "Cross"}],
        "professores": [{"id": "lia", "nome": "Lia", "avaliacao": True, "horarios": None},
                        {"id": "tom", "nome": "Tom", "avaliacao": False, "horarios": None}],
        "salas": [{"id": "s1", "nome": "Sala"}],
        "planos": [{"id": "quinzenal", "nome": "Quinzenal", "preco": 80.0, "vigencia_dias": 15, "aulas": None},
                   {"id": "pacote3", "nome": "Pacote 3 aulas", "preco": 60.0, "vigencia_dias": 45, "aulas": 3}],
        "grade": [{"id": "yoga-ter-18", "modalidade": "yoga", "professor": "lia", "sala": "s1", "dia": "ter", "hora": "18:00", "duracao_min": 60, "vagas": 1},
                  {"id": "cross-qui-7", "modalidade": "cross", "professor": "tom", "sala": "s1", "dia": "qui", "hora": "07:00", "duracao_min": 45, "vagas": 2}],
        "exercicios": [{"id": "rosca", "nome": "Rosca direta", "apelidos": ["rosca"], "grupo": "bracos",
                        "passos": ["Segure os halteres com as palmas para a frente.", "Dobre os cotovelos sem mover os ombros."],
                        "erros_comuns": [], "cuidados": []}],
        "faq": [{"id": "chuveiro", "perguntas": ["tem chuveiro"], "resposta": "Sim, dois vestiários com chuveiro."}],
    }
    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp)
        (d / "academia.json").write_text(json.dumps(cfg, ensure_ascii=False))
        s = Servidor(d, agora="2026-11-03T06:00")
        api = None
        try:
            api = s.subir()
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException as e:            # pytest.fail levanta uma BaseException: vira item da lista, não traceback
            confere(False, f"servidor não subiu com a academia nunca vista: {str(e)[:200]}")
        try:
            if api is None:
                raise _Pular()
            T = "outro-token-xyz"

            def post(rota, corpo):
                return api.req("POST", rota, corpo, token=T)

            def get(rota):
                return api.req("GET", rota, None, token=T)

            def msg(tel, texto):
                return "\n".join(api.req("POST", "/api/mensagens", {"telefone": tel, "texto": texto}, token=None)[1]["respostas"])

            confere(api.req("GET", "/api/saida", None, token="segredo-teste")[0] == 401, "token do fixture aceito")
            st, r = api.req("GET", "/api/aulas?data=2026-11-03", None, token=None)
            confere([(a["aula_id"], a["inicio"], a["vagas"]) for a in r.get("aulas", [])] == [("yoga-ter-18", "2026-11-03T18:00", 1)], f"grade nova: {r}")
            confere(api.req("GET", "/api/aulas?data=2026-11-19", None, token=None)[1].get("aulas") == [], "feriado novo ignorado")
            confere([a["aula_id"] for a in api.req("GET", "/api/aulas?data=2026-11-12", None, token=None)[1].get("aulas", [])] == ["cross-qui-7"], "quinta sem aula")

            st, a = post("/api/alunos", {"nome": "Alice", "telefone": "11987654321", "consentimento_marketing": True})
            confere(st == 201, f"aluno novo: {st} {a}")
            A, codA = a.get("id"), a.get("codigo")
            st, m = post("/api/matriculas", {"aluno_id": A, "plano": "quinzenal"})
            confere(st == 201 and m.get("fim") == "2026-11-17", f"quinzenal 03/11 + 15 − 1 = 17/11: {m}")   # 03/11 + 14 = 17/11
            st, b = post("/api/alunos", {"nome": "Beto", "telefone": "11987654322"})
            B = b.get("id")
            post("/api/matriculas", {"aluno_id": B, "plano": "quinzenal"})
            st, c = post("/api/alunos", {"nome": "Cris", "telefone": "11987654323"})
            C = c.get("id")
            st, mc = post("/api/matriculas", {"aluno_id": C, "plano": "pacote3"})
            confere(st == 201 and mc.get("aulas_restantes") == 3 and mc.get("fim") == "2026-12-17", f"pacote3: {mc}")   # 03/11 + 44 = 17/12

            st, r = post("/api/reservas", {"aluno_id": A, "aula_id": "yoga-ter-18", "data": "2026-11-03"})
            confere(st == 201, f"reserva yoga hoje 18:00 → {st} {r}")
            st, r = post("/api/reservas", {"aluno_id": B, "aula_id": "yoga-ter-18", "data": "2026-11-03"})
            confere(st == 409 and r.get("motivo") == "lotada", f"1 vaga: {st} {r}")
            st, r = post("/api/reservas", {"aluno_id": A, "aula_id": "cross-qui-7", "data": "2026-11-05"})
            confere(st == 201, f"cross 05/11 (hoje + 2 ≤ 3): {st} {r}")
            st, r = post("/api/reservas", {"aluno_id": A, "aula_id": "cross-qui-7", "data": "2026-11-12"})
            confere(st == 422 and r.get("motivo") == "antecedencia", f"12/11 > hoje + 3: {st} {r}")
            st, r = post("/api/reservas", {"aluno_id": C, "aula_id": "cross-qui-7", "data": "2026-11-05"})
            confere(st == 201 and r.get("aulas_restantes") == 2, f"crédito do pacote: {st} {r}")

            st, r = post("/api/checkins", {"codigo": codA})
            confere(st == 201, f"check-in por código novo: {st} {r}")
            confere(post("/api/checkins", {"codigo": "000000"})[0] == 404, "código inexistente")

            st, r = post("/api/tarefas/rodar", {"agora": "2026-11-12T08:00"})          # 12/11: 9 dias, aviso só a partir de 14/11
            confere(r.get("enviadas") == 0 and r.get("presencas") == 3, f"rodada 12/11 (presenças yoga 03 + cross 05): {r}")
            st, r = post("/api/tarefas/rodar", {"agora": "2026-11-13T08:00"})          # 13/11 − 03/11 = 10 → reativação
            confere(r.get("enviadas") == 1, f"reativação com 10 dias: {r}")
            st, r = post("/api/tarefas/rodar", {"agora": "2026-11-14T08:00"})          # fim 17/11 − 3 = 14/11 → vencimento de Alice e Beto
            confere(r.get("enviadas") == 2, f"vencimento com 3 dias (2 quinzenais): {r}")
            st, saida = get("/api/saida")
            tipos = sorted(m["tipo"] for m in saida.get("mensagens", []) if m.get("aluno_id") == A)
            confere(tipos == ["reativacao", "vencimento"], f"tipos para Alice: {tipos}")
            st, res = get("/api/reservas?de=2026-11-01&ate=2026-11-30")
            stt = sorted((x["aluno_id"], x["status"]) for x in res.get("reservas", []))
            confere(stt == sorted([(A, "presente"), (A, "falta"), (C, "falta")]), f"presença/falta automática: {stt}")

            st, rx = get("/api/raiox?mes=2026-11")
            v = rx.get("valores", {})
            # nov/2026: ter yoga 1 vaga × 4 (3, 10, 17, 24) + qui cross 2 × 3 (5, 12, 26; 19 feriado) = 10 vagas; 3 reservas ativas
            confere(rx.get("pacote") == "servicos" and v.get("atendimentos_mes") == 1 and v.get("falta_pct") == 66.7
                    and abs(v.get("ocupacao_pct", -1) - 30.0) <= 0.06 and v.get("clientes_novos_mes") == 3
                    and rx.get("indicadores", {}).get("alunos_ativos") == 1 and v.get("atendimentos_mes_recorrente") == 1.0,
                    f"raiox nov: {rx}")

            confere(msg("11987654321", "tem chuveiro?") == "Sim, dois vestiários com chuveiro.", "FAQ novo não respondido")
            st, r = post("/api/campanhas", {"texto": "Resultado garantido em 2 semanas"})
            confere(st == 422 and r.get("violacoes") == ["promessa_resultado"], f"trava: {st} {r}")
            t = msg("11987654321", "como faz a rosca?")
            confere(t.splitlines()[0] == "Rosca direta" and "Veja a animação" not in t, f"exercício sem SVG pelo chat: {t!r}")
            confere(api.req("GET", "/exercicios/rosca", None, token=None)[0] == 200, "página de exercício sem SVG")
            confere(api.raw("/exercicios/rosca.svg")[0] == 404, "svg inexistente deveria dar 404")
            st, ctype, corpo = api.raw("/exercicios/prancha.svg")
            confere(st == 200 and ctype.startswith("image/svg+xml") and b"<svg" in corpo, "svg do repo não servido")
            confere(api.req("GET", "/exercicios/prancha", None, token=None)[0] == 404, "exercício fora do catálogo desta academia deveria dar 404")

            # avaliação: Lia usa o horário da academia (07:00–21:00), passo 20, duração 40; dá yoga ter 18:00–19:00
            st, r = api.req("GET", "/api/avaliacoes/horarios?data=2026-11-03", None, token=None)
            hs = [h["inicio"][11:] for h in r.get("horarios", [])]
            confere(hs[:1] == ["07:00"] and hs[-1:] == ["20:20"] and len(hs) == 37 and "17:20" in hs
                    and not {"17:40", "18:00", "18:20", "18:40"} & set(hs) and "19:00" in hs, f"grade de avaliação 20 min: {hs}")
            st, av = post("/api/avaliacoes", {"aluno_id": A, "inicio": "2026-11-03T07:00", "professor": "lia"})
            confere(st == 201 and av.get("fim") == "2026-11-03T07:40", f"avaliação de 40 min: {st} {av}")
            confere(post("/api/avaliacoes", {"aluno_id": B, "inicio": "2026-11-03T07:20", "professor": "lia"})[0] == 409, "sobreposição de avaliação")
        except _Pular:
            pass
        except Exception as e:                # resposta com formato inesperado etc.: item da lista, não traceback
            confere(False, f"erro ao conferir a academia nunca vista: {e!r}")
        finally:
            s.parar()

    # 3. prova de movimento (3 SVGs do repo) — pasta temporária DENTRO do repo (chromium do snap não enxerga /tmp)
    svgs = [RAIZ / "web" / "exercicios" / f"{n}.svg" for n in ("agachamento", "prancha", "polichinelo")]
    movimento = "pulado"
    if all(p.exists() for p in svgs):
        with tempfile.TemporaryDirectory(dir=RAIZ, prefix=".verif-svg-") as tmp:
            via, res = prova_movimento(svgs, pathlib.Path(tmp))
        if via is None:
            print("PULADO: movimento dos SVGs (nenhum Chromium calibrou: instale Playwright ou um chrome completo para provar que se mexem)")
        else:
            movimento = via
            for nome, ok in res.items():
                confere(ok, f"SVG não se mexe (quadros iguais em {INSTANTES_MS} ms, via {via}): {nome}")
            print(f"MOVIMENTO: {via} — {sum(res.values())}/{len(res)} SVGs com quadros diferentes")
    else:
        confere(False, "faltam SVGs para a prova de movimento (agachamento, prancha, polichinelo)")

    # 4. HyperFrames (render local de 1 exercício) — só se estiver instalado; nunca baixa pacote
    hyper = "pulado"
    ferramenta = RAIZ / "tools" / "render-exercicios"
    tem_hf = False
    if shutil.which("npx"):
        try:
            tem_hf = subprocess.run(["npx", "--no-install", "hyperframes", "--version"], capture_output=True, timeout=120).returncode == 0
        except Exception:
            tem_hf = False
    if not shutil.which("npx"):
        print("PULADO: hyperframes (npx/Node não instalado)")
    elif not tem_hf:
        print("PULADO: hyperframes (pacote não instalado: `npx --no-install hyperframes --version` falhou; `npm install hyperframes` na raiz)")
    elif not shutil.which("ffprobe"):
        print("PULADO: hyperframes (ffprobe não instalado)")
    elif not ferramenta.exists():
        confere(False, "falta tools/render-exercicios (seção 7.4)")
    else:
        with tempfile.TemporaryDirectory() as tmp:
            try:
                r = subprocess.run([str(ferramenta), "--ids", "prancha", "--saida", tmp], cwd=RAIZ, capture_output=True, text=True, timeout=900)
                mp4 = pathlib.Path(tmp) / "prancha.mp4"
                confere(r.returncode == 0 and mp4.exists(), f"render-exercicios falhou: rc={r.returncode} {r.stderr[-300:]}")
                if mp4.exists():
                    pr = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(mp4)],
                                        capture_output=True, text=True, timeout=120)
                    info = json.loads(pr.stdout or "{}")
                    vids = [x for x in info.get("streams", []) if x.get("codec_type") == "video"]
                    auds = [x for x in info.get("streams", []) if x.get("codec_type") == "audio"]
                    dur = float(info.get("format", {}).get("duration", 0))
                    confere(vids and vids[0].get("width") == 720 and vids[0].get("height") == 720, f"mp4 não é 720×720: {vids}")
                    confere(3.5 <= dur <= 4.5, f"duração do mp4 fora de 3,5–4,5 s: {dur}")
                    confere(not auds, "mp4 com stream de áudio")
                    hyper = "ok"
            except Exception as e:
                confere(False, f"render com HyperFrames: {e!r}")
        print(f"HYPERFRAMES: {hyper}")

    # 5. container de verdade (precisa de docker; baixa a imagem python na 1ª vez)
    docker = "pulado"
    if not shutil.which("docker"):
        print("PULADO: docker (não instalado — instale ou rode a verificação numa máquina com Docker)")
    else:
        try:
            b = subprocess.run(["docker", "build", "-q", "-t", "atende-academia-verif", "."], cwd=RAIZ, capture_output=True, text=True, timeout=1800)
            confere(b.returncode == 0, f"docker build falhou: {b.stderr[-300:]}")
            if b.returncode == 0:
                c = subprocess.run(["docker", "run", "-d", "--rm", "-p", "127.0.0.1::8080", "atende-academia-verif"],
                                   capture_output=True, text=True, timeout=120)
                cid = c.stdout.strip()
                if not cid:
                    confere(False, f"docker run falhou: {c.stderr[-300:]}")
                else:
                    try:
                        porta = subprocess.run(["docker", "port", cid, "8080"], capture_output=True, text=True, timeout=60).stdout.split(":")[-1].strip()
                        ok = False
                        for _ in range(40):
                            try:
                                ok = urllib.request.urlopen(f"http://127.0.0.1:{porta}/api/saude", timeout=2).status == 200
                                break
                            except Exception:
                                time.sleep(0.5)
                        confere(ok, "container não respondeu /api/saude")
                        if ok:
                            try:
                                svg_ok = urllib.request.urlopen(f"http://127.0.0.1:{porta}/exercicios/prancha.svg", timeout=2).status == 200
                            except Exception:
                                svg_ok = False
                            confere(svg_ok, "container não serve os SVGs (COPY web/ no Dockerfile)")
                            docker = "ok" if svg_ok else docker
                    finally:
                        subprocess.run(["docker", "stop", cid], capture_output=True, timeout=120)
        except Exception as e:
            confere(False, f"docker: {e!r}")
        print(f"DOCKER: {docker}")

    if falhas:
        print("INDEPENDENTE FALHOU:")
        for f in falhas:
            print(" -", f)
        sys.exit(1)
    print(f"INDEPENDENTE OK (movimento: {movimento}, hyperframes: {hyper}, docker: {docker})")


if __name__ == "__main__":
    main()
