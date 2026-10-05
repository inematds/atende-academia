"""Testes de aceitação caixa-preta do atende-academia (contrato: docs/ESPECIFICACAO.md).

Sobem `./atende serve --porta 0 --dados <tmp>` com relógio fixo e falam só HTTP/CLI,
então valem para qualquer linguagem de implementação.
"""
import json
import os
import pathlib
import shutil
import signal
import subprocess
import threading
import unicodedata
import urllib.error
import urllib.request

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "academia.json"
TOKEN = "segredo-teste"
AGORA = "2026-10-06T09:00"  # terça-feira


def norm(s):
    """Minúsculas, sem acento (o mesmo que a seção 11 faz antes de decidir)."""
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


class Cliente:
    def __init__(self, base):
        self.base = base

    def req(self, metodo, rota, corpo=None, token=TOKEN):
        dados = None if corpo is None else json.dumps(corpo).encode()
        r = urllib.request.Request(self.base + rota, data=dados, method=metodo)
        if dados is not None:
            r.add_header("Content-Type", "application/json")
        if token:
            r.add_header("X-Token", token)
        try:
            with urllib.request.urlopen(r, timeout=10) as resp:
                texto = resp.read().decode()
                return resp.status, (json.loads(texto) if texto and "json" in resp.headers.get("Content-Type", "") else texto)
        except urllib.error.HTTPError as e:
            texto = e.read().decode()
            try:
                return e.code, json.loads(texto)
            except ValueError:
                return e.code, texto

    def raw(self, rota):
        """GET cru: (status, Content-Type, bytes) — para SVG/MP4."""
        r = urllib.request.Request(self.base + rota, method="GET")
        try:
            with urllib.request.urlopen(r, timeout=10) as resp:
                return resp.status, resp.headers.get("Content-Type", ""), resp.read()
        except urllib.error.HTTPError as e:
            return e.code, e.headers.get("Content-Type", ""), e.read()

    def get(self, rota, **kw):
        return self.req("GET", rota, **kw)

    def post(self, rota, corpo=None, **kw):
        return self.req("POST", rota, {} if corpo is None else corpo, **kw)

    def put(self, rota, corpo, **kw):
        return self.req("PUT", rota, corpo, **kw)

    def delete(self, rota, **kw):
        return self.req("DELETE", rota, **kw)

    # atalhos (padrões vêm do fixture; no verificar-independente.py passar tudo explícito)
    def aluno(self, nome="Maria Silva", telefone="(41) 99999-0001", marketing=False):
        st, r = self.post("/api/alunos", {"nome": nome, "telefone": telefone, "consentimento_marketing": marketing})
        assert st in (200, 201), (st, r)
        return r["id"]

    def codigo(self, aluno_id):
        st, r = self.get("/api/alunos")
        assert st == 200, (st, r)
        return next(a["codigo"] for a in r["alunos"] if a["id"] == aluno_id)

    def matricula(self, aluno_id, plano="mensal", inicio=None):
        corpo = {"aluno_id": aluno_id, "plano": plano}
        if inicio:
            corpo["inicio"] = inicio
        return self.post("/api/matriculas", corpo)

    def ativo(self, nome="Maria Silva", telefone="(41) 99999-0001", plano="mensal", inicio=None, marketing=False):
        """Aluno com matrícula ativa (padrão: mensal a partir de hoje)."""
        aid = self.aluno(nome, telefone, marketing)
        st, r = self.matricula(aid, plano, inicio)
        assert st == 201, (st, r)
        return aid

    def reserva(self, aluno_id, aula_id, data):
        return self.post("/api/reservas", {"aluno_id": aluno_id, "aula_id": aula_id, "data": data})

    def checkin(self, codigo):
        return self.post("/api/checkins", {"codigo": codigo})

    def msg(self, telefone, texto):
        st, r = self.post("/api/mensagens", {"telefone": telefone, "texto": texto}, token=None)
        assert st == 200, (st, r)
        return "\n".join(r["respostas"])

    def saida(self, tipo=None):
        st, r = self.get("/api/saida")
        assert st == 200, (st, r)
        return [m for m in r["mensagens"] if tipo is None or m["tipo"] == tipo]

    def rodar(self, agora=None):
        st, r = self.post("/api/tarefas/rodar", {"agora": agora} if agora else {})
        assert st == 200, (st, r)
        return r

    def aulas(self, data):
        st, r = self.get(f"/api/aulas?data={data}", token=None)
        assert st == 200, (st, r)
        return r["aulas"]

    def ocorrencia(self, data, aula_id):
        return next(a for a in self.aulas(data) if a["aula_id"] == aula_id)


SERVIDORES = []


@pytest.fixture(autouse=True)
def _parar_servidores():
    """Para todo Servidor criado no teste, mesmo que uma asserção falhe antes do parar() explícito
    (evita `atende serve` órfão quando o teste sobe o servidor fora de try/finally)."""
    yield
    while SERVIDORES:
        SERVIDORES.pop().parar()


class Servidor:
    def __init__(self, dados, agora=AGORA, env=None):
        SERVIDORES.append(self)  # o teardown autouse para todos, mesmo se o teste falhar
        self.dados = dados
        self.agora = agora
        self.env = env or {}
        self.proc = None

    def subir(self):
        exe = RAIZ / "atende"
        if not exe.exists():
            pytest.fail("./atende não existe (ponto de entrada da seção 1 da especificação)")
        env = {k: v for k, v in os.environ.items()
               if not k.startswith(("EVOLUTION_", "TELEGRAM_", "WEBHOOK_", "PUBLIC_URL", "EXERCICIOS_", "ATENDE_"))}
        env.update(ATENDE_AGORA=self.agora, **self.env)
        self.proc = subprocess.Popen(
            [str(exe), "serve", "--porta", "0", "--dados", str(self.dados)],
            cwd=RAIZ, env=env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
        )
        linha = {}

        def ler():
            linha["v"] = self.proc.stdout.readline()

        t = threading.Thread(target=ler, daemon=True)
        t.start()
        t.join(15)
        primeira = (linha.get("v") or "").strip()
        if not primeira.startswith("PORTA="):
            self.parar()
            pytest.fail(f"servidor não imprimiu PORTA=<n> na 1ª linha (veio {primeira!r})")
        # drena o resto do stdout para o processo não travar com o pipe cheio
        threading.Thread(target=lambda: [None for _ in self.proc.stdout], daemon=True).start()
        return Cliente(f"http://127.0.0.1:{int(primeira.split('=', 1)[1])}")

    def parar(self):
        if self.proc and self.proc.poll() is None:
            self.proc.send_signal(signal.SIGTERM)
            try:
                self.proc.wait(5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(5)


@pytest.fixture
def dados(tmp_path):
    d = tmp_path / "dados"
    d.mkdir()
    shutil.copy(FIXTURE, d / "academia.json")
    return d


@pytest.fixture
def servidor(dados):
    s = Servidor(dados)
    yield s
    s.parar()


@pytest.fixture
def api(servidor):
    return servidor.subir()


class Externo:
    """Servidor falso local que faz o papel da Evolution API e da API do Telegram. Grava cada pedido."""

    def __init__(self):
        import http.server
        self.pedidos = []
        self.falhas = 0          # quantos próximos pedidos devolvem 500
        self.prox_msg = 1000
        self.trava = threading.Lock()
        externo = self

        class H(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                corpo = self.rfile.read(int(self.headers.get("Content-Length") or 0))
                try:
                    dados = json.loads(corpo or b"{}")
                except ValueError:
                    dados = {}
                pedido = {"rota": self.path, "headers": {k.lower(): v for k, v in self.headers.items()}, "json": dados}
                with externo.trava:
                    if externo.falhas > 0:
                        externo.falhas -= 1
                        pedido["status"] = 500
                        externo.pedidos.append(pedido)
                        self.send_response(500)
                        self.send_header("Content-Length", "0")
                        self.end_headers()
                        return
                    externo.prox_msg += 1
                    pedido["status"], pedido["message_id"] = 200, externo.prox_msg
                    externo.pedidos.append(pedido)
                resp = {"ok": True, "result": {"message_id": pedido["message_id"]}, "key": {"id": f"X{pedido['message_id']}"}}
                b = json.dumps(resp).encode()
                self.send_response(201 if "/message/" in self.path else 200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)

            def log_message(self, *a):
                pass

        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def whats(self, ok=True):
        return [p for p in self.pedidos if p["rota"] == "/message/sendText/academia" and (not ok or p["status"] == 200)]

    def whats_media(self):
        return [p for p in self.pedidos if p["rota"] == "/message/sendMedia/academia" and p["status"] == 200]

    def telegram(self):
        return [p for p in self.pedidos if p["rota"] == "/botTOKEN123/sendMessage" and p["status"] == 200]

    def fechar(self):
        self.srv.shutdown()
        self.srv.server_close()


SEGREDO_WH = "wh-segredo"
CHAT_EQUIPE = -100777
SEGREDO_TG = "tg-segredo"


def env_integracoes(externo):
    return {
        "EVOLUTION_URL": externo.url, "EVOLUTION_API_KEY": "chave-evo", "EVOLUTION_INSTANCIA": "academia",
        "WEBHOOK_SEGREDO": SEGREDO_WH,
        "TELEGRAM_API_URL": externo.url, "TELEGRAM_TOKEN": "TOKEN123", "TELEGRAM_CHAT_ID": str(CHAT_EQUIPE),
        "TELEGRAM_SEGREDO": SEGREDO_TG,
    }


@pytest.fixture
def externo():
    e = Externo()
    yield e
    e.fechar()


@pytest.fixture
def api_int(dados, externo):
    """Servidor com Evolution e Telegram apontando para o falso local."""
    s = Servidor(dados, env=env_integracoes(externo))
    yield s.subir()
    s.parar()


def esperar(cond, segundos=5):
    import time
    fim = time.time() + segundos
    while time.time() < fim:
        if cond():
            return True
        time.sleep(0.05)
    return cond()
