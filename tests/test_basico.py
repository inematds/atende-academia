"""Seções 1, 9, 10 (saúde/planos/modalidades), 17 e persistência. Agora = ter 06/10/2026 09:00."""
from conftest import RAIZ, Servidor


def test_saude_traz_versao_do_arquivo(api):
    st, r = api.get("/api/saude", token=None)
    assert st == 200
    assert r["ok"] is True
    assert r["versao"] == (RAIZ / "VERSION").read_text().strip()


def test_planos_e_modalidades_publicos_na_ordem(api):
    st, r = api.get("/api/planos", token=None)
    assert st == 200
    assert [p["id"] for p in r["planos"]] == ["mensal", "trimestral", "anual", "avulso5"]
    assert r["planos"][0]["vigencia_dias"] == 30 and r["planos"][0]["aulas"] is None
    assert r["planos"][3]["aulas"] == 5 and r["planos"][3]["preco"] == 99.0
    st, r = api.get("/api/modalidades", token=None)
    assert st == 200
    assert [m["id"] for m in r["modalidades"]] == ["musculacao", "spinning", "pilates", "funcional"]


def test_rotas_da_equipe_exigem_token_e_publicas_nao(api):
    for metodo, rota in [("GET", "/api/saida"), ("GET", "/api/reservas?data=2026-10-07"), ("POST", "/api/alunos"),
                         ("POST", "/api/matriculas"), ("POST", "/api/reservas"), ("POST", "/api/checkins"),
                         ("GET", "/api/checkins?de=2026-10-06&ate=2026-10-06"), ("GET", "/api/atendimento-humano"),
                         ("GET", "/api/raiox?mes=2026-10"), ("POST", "/api/campanhas"), ("GET", "/api/aulas?de=2026-10-06&ate=2026-10-07"),
                         ("POST", "/api/avaliacoes"), ("GET", "/api/grade"), ("POST", "/api/exercicios")]:
        corpo = {} if metodo == "POST" else None   # corpo vazio: o 401 vem antes de qualquer validação (seção 9)
        assert api.req(metodo, rota, corpo, token=None)[0] == 401, rota
        assert api.req(metodo, rota, corpo, token="errado")[0] == 401, rota
    assert api.get("/api/aulas?data=2026-10-07", token=None)[0] == 200
    assert api.get("/api/planos", token=None)[0] == 200
    assert api.get("/api/exercicios", token=None)[0] == 200
    assert api.get("/api/exercicios/prancha", token=None)[0] == 200
    assert api.get("/api/avaliacoes/horarios?data=2026-10-07", token=None)[0] == 200
    assert api.post("/api/mensagens", {"telefone": "41911112222", "texto": "oi"}, token=None)[0] == 200


def test_paginas(api):
    st, html = api.get("/", token=None)
    assert st == 200 and 'id="chat"' in html
    st, html = api.get("/equipe", token=None)
    assert st == 200
    for el in ("grade", "reservas", "checkins", "alunos", "planos", "fichas", "biblioteca", "fila-humano", "saida"):
        assert f'id="{el}"' in html, el
    st, html = api.get("/exercicios/prancha", token=None)
    assert st == 200
    assert "<h1" in html and "Prancha" in html
    assert "Antebraços no chão" in html and "<ol" in html and "<li" in html   # passos numerados
    assert "/exercicios/prancha.svg" in html
    assert api.get("/exercicios/xyz", token=None)[0] == 404


def test_estado_persiste_ao_reiniciar(dados):
    s = Servidor(dados)
    api = s.subir()
    aid = api.ativo()
    st, r = api.reserva(aid, "pil-qua-9", "2026-10-07")
    assert st == 201, r
    s.parar()
    s2 = Servidor(dados)
    try:
        api2 = s2.subir()
        st, lista = api2.get("/api/reservas?data=2026-10-07")
        assert st == 200
        assert [x["id"] for x in lista["reservas"]] == [r["id"]]
        st, r2 = api2.reserva(aid, "pil-qua-9", "2026-10-07")
        assert st == 409 and r2["motivo"] == "ja_reservada"
    finally:
        s2.parar()


def test_cria_dados_e_academia_json_do_exemplo_se_faltar(tmp_path):
    d = tmp_path / "novo" / "dados"   # nem o diretório existe: o servidor cria (seção 1)
    s = Servidor(d)
    try:
        api = s.subir()
        assert api.get("/api/saude", token=None)[0] == 200
        assert (d / "academia.json").exists()
        st, r = api.get("/api/planos", token=None)
        assert [p["id"] for p in r["planos"]] == ["mensal", "trimestral", "anual", "avulso5"]
    finally:
        s.parar()
