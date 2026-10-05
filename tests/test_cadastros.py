"""Seções 18 e 19: cadastros da equipe (professores, grade, exercícios, FAQ), semente e banco de dados."""
import subprocess

from conftest import RAIZ, Servidor, norm


def horarios(api, data, professor=None):
    rota = f"/api/avaliacoes/horarios?data={data}" + (f"&professor={professor}" if professor else "")
    st, r = api.get(rota, token=None)
    assert st == 200, (st, r)
    return [(h["inicio"][11:], h["professor"]) for h in r["horarios"]]


def test_professor_crud(api):
    vazio = {d: [] for d in ("seg", "ter", "qua", "qui", "sex", "sab", "dom")}
    st, r = api.post("/api/professores", {"id": "eva", "nome": "Eva", "avaliacao": True, "horarios": dict(vazio, qua=[["14:00", "16:00"]])})
    assert st == 201, r
    assert [h for h, p in horarios(api, "2026-10-07", "eva")] == ["14:00", "14:30", "15:00", "15:30"]
    assert horarios(api, "2026-10-08", "eva") == []
    assert api.post("/api/professores", {"id": "eva", "nome": "X"})[0] == 409
    assert api.put("/api/professores/naoexiste", {"nome": "Q"})[0] == 404
    st, lista = api.get("/api/professores")
    assert [p["id"] for p in lista["professores"]] == ["carla", "diego", "eva"]
    aid = api.aluno()
    assert api.post("/api/avaliacoes", {"aluno_id": aid, "inicio": "2026-10-07T14:00", "professor": "eva"})[0] == 201
    st, r = api.delete("/api/professores/eva")
    assert st == 200 and r["ativo"] is False
    assert horarios(api, "2026-10-07", "eva") == []
    assert api.post("/api/avaliacoes", {"aluno_id": aid, "inicio": "2026-10-07T15:00", "professor": "eva"})[0] == 422
    assert len(api.get(f"/api/alunos/{aid}/avaliacoes")[1]["avaliacoes"]) == 1   # a já marcada continua


def test_grade_crud(api):
    nova = {"id": "pil-qui-8", "modalidade": "pilates", "professor": "carla", "sala": "sala2", "dia": "qui", "hora": "08:00", "duracao_min": 60, "vagas": 5}
    st, r = api.post("/api/grade", nova)
    assert st == 201, r
    o = api.ocorrencia("2026-10-08", "pil-qui-8")
    assert (o["inicio"], o["livres"], o["modalidade"]) == ("2026-10-08T08:00", 5, "Pilates")
    assert api.post("/api/grade", nova)[0] == 409
    assert api.post("/api/grade", dict(nova, id="x1", modalidade="xyz"))[0] == 422
    assert api.post("/api/grade", dict(nova, id="x2", dia="xyz"))[0] == 400
    assert [g["id"] for g in api.get("/api/grade")[1]["grade"]][-1] == "pil-qui-8"
    aid = api.ativo()
    _, res = api.reserva(aid, "pil-qui-8", "2026-10-08")
    st, r = api.delete("/api/grade/pil-qui-8")
    assert st == 200 and r["ativo"] is False
    assert [a["aula_id"] for a in api.aulas("2026-10-08")] == []
    assert api.get("/api/reservas?data=2026-10-08")[1]["reservas"][0]["status"] == "reservada"   # reserva feita continua
    assert api.put("/api/grade/pil-qua-9", {"vagas": 3})[0] == 200
    assert api.ocorrencia("2026-10-07", "pil-qua-9")["livres"] == 3


def test_exercicio_editar_e_desativar(api):
    st, r = api.put("/api/exercicios/prancha", {"apelidos": ["prancha abdominal", "plank", "tabua"]})
    assert st == 200 and "tabua" in r["apelidos"]
    assert api.msg("41988887777", "como faz a tabua?").splitlines()[0] == "Prancha"
    st, r = api.delete("/api/exercicios/polichinelo")
    assert st == 200 and r["ativo"] is False
    assert "polichinelo" not in [e["id"] for e in api.get("/api/exercicios", token=None)[1]["exercicios"]]
    assert api.get("/api/exercicios/polichinelo", token=None)[1]["ativo"] is False
    assert "nao entendi" in norm(api.msg("41988887777", "explica o polichinelo"))
    aid = api.aluno()
    assert api.put(f"/api/alunos/{aid}/ficha", {"treinos": [{"nome": "A", "itens": [{"exercicio": "polichinelo", "series": 3, "repeticoes": 20}]}]})[0] == 422
    assert api.put("/api/exercicios/xyz", {"nome": "X"})[0] == 404


def test_faq_crud_vale_na_hora(api):
    st, r = api.post("/api/faq", {"perguntas": ["atendem criança"], "resposta": "Sim, a partir de 12 anos com autorização."})
    assert st == 201
    assert api.msg("41988887777", "vocês atendem criança?") == "Sim, a partir de 12 anos com autorização."
    assert api.delete(f"/api/faq/{r['id']}")[0] == 204
    assert api.msg("41988887777", "vocês atendem criança?") != "Sim, a partir de 12 anos com autorização."
    ids = [f["id"] for f in api.get("/api/faq")[1]["faq"]]
    assert "estacionamento" in ids and r["id"] not in ids


def test_semente_so_na_primeira_vez(dados):
    s = Servidor(dados)
    api = s.subir()
    assert api.post("/api/planos", {"id": "semestral", "nome": "Semestral", "preco": 599, "vigencia_dias": 180})[0] == 201
    api.delete("/api/exercicios/polichinelo")
    s.parar()
    s2 = Servidor(dados)
    try:
        api2 = s2.subir()
        assert [p["id"] for p in api2.get("/api/planos", token=None)[1]["planos"]] == ["mensal", "trimestral", "anual", "avulso5", "semestral"]
        assert "polichinelo" not in [e["id"] for e in api2.get("/api/exercicios", token=None)[1]["exercicios"]]
    finally:
        s2.parar()


def test_backup_e_restaurar(dados, tmp_path):
    s = Servidor(dados)
    api = s.subir()
    aid = api.ativo("Guardada", "41999990009")
    api.reserva(aid, "pil-qua-9", "2026-10-07")
    arq = tmp_path / "copia.bak"
    r = subprocess.run([str(RAIZ / "atende"), "backup", "--dados", str(dados), "--saida", str(arq)],
                       cwd=RAIZ, capture_output=True, timeout=30)
    assert r.returncode == 0 and arq.exists() and arq.stat().st_size > 0
    api.delete(f"/api/alunos/{aid}")
    api.aluno("Depois do backup", "41999990010")
    s.parar()
    r = subprocess.run([str(RAIZ / "atende"), "restaurar", "--dados", str(dados), "--entrada", str(arq)],
                       cwd=RAIZ, capture_output=True, timeout=30)
    assert r.returncode == 0
    s2 = Servidor(dados)
    try:
        api2 = s2.subir()
        nomes = [p["nome"] for p in api2.get("/api/alunos")[1]["alunos"]]
        assert nomes == ["Guardada"]
        assert len(api2.get("/api/reservas?data=2026-10-07")[1]["reservas"]) == 1
    finally:
        s2.parar()
