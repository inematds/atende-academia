"""Seções 7.3, 20 e 21: WhatsApp pela Evolution API (inclusive MP4 por sendMedia) e atendimento interno pelo Telegram,
contra servidor falso local. Agora = ter 06/10/2026 09:00."""
import json
import time
import urllib.error
import urllib.request

from conftest import CHAT_EQUIPE, SEGREDO_TG, SEGREDO_WH, Servidor, env_integracoes, esperar, norm

TEL = "41988887777"
NUM = "5541988887777"
ESTAC = "Temos estacionamento próprio para 20 carros, sem custo."

_ids = iter(range(1, 10 ** 6))


def evo(api, texto=None, numero=NUM, msg_id=None, from_me=False, sufixo="@s.whatsapp.net",
        evento="messages.upsert", message=None):
    if message is None:
        message = {"conversation": texto}
    corpo = {"event": evento, "instance": "academia",
             "data": {"key": {"remoteJid": numero + sufixo, "fromMe": from_me, "id": msg_id or f"M{next(_ids)}"},
                      "pushName": "Aluno", "message": message, "messageType": "conversation"}}
    st, _ = api.post(f"/webhook/evolution/{SEGREDO_WH}", corpo, token=None)
    assert st == 200
    return corpo


def tg(api, texto, reply_to=None, chat=CHAT_EQUIPE, segredo=SEGREDO_TG):
    """Entrega um update do Telegram no webhook; devolve o status HTTP."""
    msg = {"message_id": next(_ids), "chat": {"id": chat}, "from": {"id": 7, "first_name": "Rita"}, "text": texto}
    if reply_to:
        msg["reply_to_message"] = {"message_id": reply_to}
    q = urllib.request.Request(api.base + "/webhook/telegram", method="POST",
                               data=json.dumps({"update_id": next(_ids), "message": msg}).encode(),
                               headers={"Content-Type": "application/json", "X-Telegram-Bot-Api-Secret-Token": segredo})
    try:
        with urllib.request.urlopen(q, timeout=10) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code


def textos_whats(externo):
    return [p["json"]["text"] for p in externo.whats()]


def abre_atendimento(api, externo):
    api.msg(TEL, "quero falar com um atendente")
    assert esperar(lambda: len(externo.telegram()) >= 1)
    [at] = api.get("/api/atendimento-humano")[1]["fila"]
    abertura = next(p for p in externo.telegram() if f"#{at['id']}" in p["json"]["text"])
    return at, abertura


# --- WhatsApp (Evolution) ---------------------------------------------------------------

def test_webhook_evolution_segredo_errado(api_int):
    assert api_int.post("/webhook/evolution/errado", {"event": "messages.upsert"}, token=None)[0] == 404


def test_whatsapp_responde_pela_evolution(api_int, externo):
    evo(api_int, "tem estacionamento?")
    assert esperar(lambda: len(externo.whats()) == 1)
    [p] = externo.whats()
    assert p["json"]["number"] == NUM and p["json"]["text"] == ESTAC
    assert p["headers"].get("apikey") == "chave-evo"


def test_whatsapp_ignora_o_que_nao_e_do_aluno(api_int, externo):
    evo(api_int, "tem estacionamento?", msg_id="DUP1")
    evo(api_int, "tem estacionamento?", msg_id="DUP1")            # reenvio da Evolution
    evo(api_int, "tem estacionamento?", from_me=True)              # mensagem da própria academia
    evo(api_int, "tem estacionamento?", numero="1203630", sufixo="@g.us")  # grupo
    evo(api_int, "tem estacionamento?", evento="connection.update")
    time.sleep(0.8)
    assert textos_whats(externo) == [ESTAC]


def test_whatsapp_sem_texto(api_int, externo):
    evo(api_int, message={"audioMessage": {"seconds": 5}})
    assert esperar(lambda: textos_whats(externo) == ["Por enquanto só consigo ler mensagens de texto."])


def test_whatsapp_reserva_e_avisa_equipe(api_int, externo):
    api_int.ativo("Maria Lima", TEL)

    def tem(trecho):
        return esperar(lambda: any(trecho in norm(t) for t in textos_whats(externo)))

    evo(api_int, "quero reservar uma aula")
    assert tem("1) 07/10 09:00 pilates com carla")
    evo(api_int, "1")
    assert tem("reservad")
    [x] = api_int.get("/api/reservas?data=2026-10-07")[1]["reservas"]
    assert (x["telefone"], x["aula_id"], x["status"]) == ("+" + NUM, "pil-qua-9", "reservada")
    assert esperar(lambda: any("Nova reserva: 07/10 09:00 Maria Lima — Pilates" in p["json"]["text"] for p in externo.telegram()))
    assert all(str(p["json"]["chat_id"]) == str(CHAT_EQUIPE) for p in externo.telegram())


def test_saida_pela_evolution_com_reenvio(api_int, externo):
    api_int.ativo("Maria", TEL, inicio="2026-09-10")             # fim 09/10: aviso de vencimento devido hoje
    externo.falhas = 1
    r = api_int.rodar()
    assert r["enviadas"] == 1
    [m] = api_int.saida("vencimento")
    assert m["status"] == "pendente"
    r = api_int.rodar()
    assert r["enviadas"] == 0 and r["reenviadas"] == 1
    assert api_int.saida("vencimento")[0]["status"] == "enviado"
    [p] = externo.whats()
    assert p["json"]["number"] == NUM and "09/10" in p["json"]["text"]


def test_sem_evolution_status_simulado(api):
    api.ativo("Maria", TEL, inicio="2026-09-10")
    api.rodar()
    assert api.saida("vencimento")[0]["status"] == "simulado"


def test_exercicio_com_mp4_vai_por_sendmedia_e_sem_mp4_por_texto(dados, externo, tmp_path):
    pasta = tmp_path / "mp4"
    pasta.mkdir()
    (pasta / "prancha.mp4").write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64)
    env = dict(env_integracoes(externo), PUBLIC_URL="https://academia.teste", EXERCICIOS_MP4_DIR=str(pasta))
    s = Servidor(dados, env=env)
    try:
        api = s.subir()
        evo(api, "como faço a prancha?")
        assert esperar(lambda: len(externo.whats_media()) == 1)
        [p] = externo.whats_media()
        j = p["json"]
        assert (j["number"], j["mediatype"], j["media"]) == (NUM, "video", "https://academia.teste/exercicios/prancha.mp4")
        assert j["caption"].splitlines()[0] == "Prancha" and "1. Antebraços no chão" in j["caption"]
        assert "Veja a animação" not in j["caption"]
        assert p["headers"].get("apikey") == "chave-evo"
        time.sleep(0.5)
        assert not any("Prancha" in t for t in textos_whats(externo))       # nada de sendText para essa resposta
        evo(api, "me mostra o agachamento")                                 # sem MP4: texto com link absoluto
        assert esperar(lambda: any(t.splitlines()[0] == "Agachamento" for t in textos_whats(externo)))
        t = next(t for t in textos_whats(externo) if t.startswith("Agachamento"))
        assert t.splitlines()[-1] == "Veja a animação: https://academia.teste/exercicios/agachamento"
        assert len(externo.whats_media()) == 1
        # o link do sendMedia aponta para a rota que serve a pasta configurada
        st, ctype, corpo = api.raw("/exercicios/prancha.mp4")
        assert st == 200 and ctype.startswith("video/mp4") and len(corpo) == 76
    finally:
        s.parar()


# --- Telegram (equipe) ------------------------------------------------------------------

def test_abertura_vai_ao_grupo(api_int, externo):
    at, abertura = abre_atendimento(api_int, externo)
    t = abertura["json"]["text"]
    assert TEL in t.replace(" ", "").replace("-", "") and f"#{at['id']}" in t
    assert str(abertura["json"]["chat_id"]) == str(CHAT_EQUIPE)
    assert at["status"] == "aberto"


def test_alerta_marca_alta(api_int, externo):
    api_int.msg(TEL, "estou com dor forte no joelho")
    assert esperar(lambda: any("ALTA" in p["json"]["text"] for p in externo.telegram()))


def test_atendimento_aberto_silencia_bot_e_repassa(api_int, externo):
    at, abertura = abre_atendimento(api_int, externo)
    st, r = api_int.post("/api/mensagens", {"telefone": TEL, "texto": "tem estacionamento?"}, token=None)
    assert r["respostas"] == []
    assert esperar(lambda: any(p["json"].get("reply_to_message_id") == abertura["message_id"]
                               and "tem estacionamento" in p["json"]["text"] for p in externo.telegram()))
    # alerta de saúde continua respondendo
    assert "192" in api_int.msg(TEL, "agora estou com falta de ar")


def test_equipe_responde_em_cima_e_pela_pagina(api_int, externo):
    at, abertura = abre_atendimento(api_int, externo)
    assert tg(api_int, "Olá, aqui é a Rita. Como posso ajudar?", reply_to=abertura["message_id"]) == 200
    assert esperar(lambda: any(m["texto"] == "Olá, aqui é a Rita. Como posso ajudar?" for m in api_int.saida("humano")))
    assert api_int.saida("humano")[0]["telefone"] == "+" + NUM
    assert esperar(lambda: "Olá, aqui é a Rita. Como posso ajudar?" in textos_whats(externo))
    assert api_int.post(f"/api/atendimento-humano/{at['id']}/responder", {"texto": "Pode vir às 10h"})[0] == 200
    assert [m["texto"] for m in api_int.saida("humano")][-1] == "Pode vir às 10h"
    assert api_int.post(f"/api/atendimento-humano/{at['id']}/encerrar")[0] == 200
    assert api_int.get("/api/atendimento-humano")[1]["fila"] == []
    assert api_int.msg(TEL, "tem estacionamento?") == ESTAC


def test_webhook_telegram_protegido(api_int, externo):
    at, abertura = abre_atendimento(api_int, externo)
    assert tg(api_int, "invasor", reply_to=abertura["message_id"], segredo="errado") == 401
    assert tg(api_int, "outro grupo", reply_to=abertura["message_id"], chat=-1009999) == 200
    time.sleep(0.5)
    assert api_int.saida("humano") == []


def test_comandos_responder_encerrar_fila(api_int, externo):
    at, _ = abre_atendimento(api_int, externo)
    tg(api_int, f"/responder {at['id']} Já te ligo")
    assert esperar(lambda: [m["texto"] for m in api_int.saida("humano")] == ["Já te ligo"])
    n = len(externo.telegram())
    tg(api_int, "/fila")
    assert esperar(lambda: any(f"#{at['id']}" in p["json"]["text"] for p in externo.telegram()[n:]))
    tg(api_int, f"/encerrar {at['id']}")
    assert esperar(lambda: api_int.get("/api/atendimento-humano")[1]["fila"] == [])
    assert api_int.msg(TEL, "tem estacionamento?") == ESTAC


def test_comando_aulas(api_int, externo):
    aid = api_int.ativo("Maria Lima", "41999990001")
    api_int.reserva(aid, "pil-qua-9", "2026-10-07")
    tg(api_int, "/aulas 2026-10-07")

    def achou():
        ts = [p["json"]["text"] for p in externo.telegram()]
        return any("09:00 Pilates (Carla) — 1/2" in t and "19:00 Spinning (Diego) — 0/2" in t for t in ts)
    assert esperar(achou)
    n = len(externo.telegram())
    tg(api_int, "/aulas 2026-10-11")
    assert esperar(lambda: any("sem aulas" in norm(p["json"]["text"]) for p in externo.telegram()[n:]))


def test_cancelamento_pelo_chat_avisa_equipe(api_int, externo):
    aid = api_int.ativo("Maria", TEL)
    api_int.reserva(aid, "pil-qua-9", "2026-10-07")
    assert "1) 07/10 09:00 Pilates" in api_int.msg(TEL, "cancelar")
    assert "cancelad" in norm(api_int.msg(TEL, "1"))
    assert esperar(lambda: any(p["json"]["text"].startswith("Cancelada:") and "07/10 09:00" in p["json"]["text"]
                               for p in externo.telegram()))
