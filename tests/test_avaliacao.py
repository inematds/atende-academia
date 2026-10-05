"""Seção 8: avaliação física — horários, agendamento, resultado (dado sensível) e lembrete. Agora = ter 06/10/2026 09:00.
Carla faz avaliação ter/qua/qui 09:00–12:00 (passo 30, duração 30) e dá pilates qua 09:00–10:00."""
from conftest import norm


def horarios(api, data, professor=None):
    rota = f"/api/avaliacoes/horarios?data={data}" + (f"&professor={professor}" if professor else "")
    st, r = api.get(rota, token=None)
    assert st == 200, (st, r)
    return [(h["inicio"][11:], h["professor"]) for h in r["horarios"]]


def test_horarios_de_avaliacao(api):
    # qua 07/10: janela 09:00–12:00 menos a aula de pilates [09:00, 10:00)
    assert horarios(api, "2026-10-07") == [(h, "carla") for h in ("10:00", "10:30", "11:00", "11:30")]
    # ter 06/10 às 09:00 com antecedência 2 h: só a partir de 11:00
    assert horarios(api, "2026-10-06") == [("11:00", "carla"), ("11:30", "carla")]
    assert horarios(api, "2026-10-08") == [(h, "carla") for h in ("09:00", "09:30", "10:00", "10:30", "11:00", "11:30")]
    assert horarios(api, "2026-10-09") == []       # sexta: Carla não atende
    assert horarios(api, "2026-10-13", "diego") == []   # Diego não faz avaliação
    assert api.get("/api/avaliacoes/horarios?data=2026-10-07&professor=xyz", token=None)[0] == 404


def test_agendar_cancelar_409_422(api):
    aid = api.aluno()
    st, a = api.post("/api/avaliacoes", {"aluno_id": aid, "inicio": "2026-10-07T10:00", "professor": "carla"})
    assert st == 201 and (a["status"], a["fim"], a["professor"]) == ("agendada", "2026-10-07T10:30", "carla")
    assert api.post("/api/avaliacoes", {"aluno_id": aid, "inicio": "2026-10-07T10:00", "professor": "carla"})[0] == 409
    assert api.post("/api/avaliacoes", {"aluno_id": aid, "inicio": "2026-10-07T09:30", "professor": "carla"})[0] == 409  # aula de pilates
    assert api.post("/api/avaliacoes", {"aluno_id": aid, "inicio": "2026-10-07T12:00", "professor": "carla"})[0] == 422  # não cabe na janela
    assert api.post("/api/avaliacoes", {"aluno_id": aid, "inicio": "2026-10-06T10:00", "professor": "carla"})[0] == 422  # antecedência
    assert api.post("/api/avaliacoes", {"aluno_id": aid, "inicio": "2026-10-07T10:30", "professor": "diego"})[0] == 422  # não faz avaliação
    assert api.post("/api/avaliacoes", {"aluno_id": 9999, "inicio": "2026-10-07T10:30"})[0] == 404
    st, b = api.post("/api/avaliacoes", {"aluno_id": aid, "inicio": "2026-10-07T10:30"})     # sem professor: o primeiro livre
    assert st == 201 and b["professor"] == "carla"
    assert ("10:00", "carla") not in horarios(api, "2026-10-07") and ("11:00", "carla") in horarios(api, "2026-10-07")
    st, r = api.post(f"/api/avaliacoes/{a['id']}/cancelar")
    assert st == 200 and r["status"] == "cancelada"
    assert api.post("/api/avaliacoes", {"aluno_id": aid, "inicio": "2026-10-07T10:00", "professor": "carla"})[0] == 201
    st, lista = api.get(f"/api/alunos/{aid}/avaliacoes")
    assert [(x["inicio"][11:], x["status"]) for x in lista["avaliacoes"]] == [("10:00", "cancelada"), ("10:00", "agendada"), ("10:30", "agendada")]


def test_resultado_dados_sensiveis_e_chat(api):
    aid = api.aluno("Maria", "41988887777")
    _, a = api.post("/api/avaliacoes", {"aluno_id": aid, "inicio": "2026-10-07T10:00"})
    assert api.post(f"/api/avaliacoes/{a['id']}/resultado", {"altura_cm": 178})[0] == 422
    st, r = api.post(f"/api/avaliacoes/{a['id']}/resultado",
                     {"peso_kg": 80.5, "altura_cm": 178, "gordura_pct": 18.2, "medidas": {"cintura_cm": 86}, "observacoes": "ok"})
    assert st == 200 and r["status"] == "realizada"
    [x] = api.get(f"/api/alunos/{aid}/avaliacoes")[1]["avaliacoes"]
    assert x["resultado"]["peso_kg"] == 80.5 and x["resultado"]["medidas"]["cintura_cm"] == 86
    assert api.get(f"/api/alunos/{aid}/dados")[1]["avaliacoes"][0]["resultado"]["gordura_pct"] == 18.2
    r = api.msg("41988887777", "quero marcar minha avaliação física")
    assert "avaliacao" in norm(r) and "recepcao" in norm(r) and "80" not in r and "18" not in r
    assert api.delete(f"/api/alunos/{aid}")[0] == 204
    assert api.get(f"/api/alunos/{aid}/dados")[1]["avaliacoes"][0]["resultado"] is None


def test_lembrete_avaliacao_uma_vez(api):
    aid = api.aluno("Maria", "41999990001")
    api.post("/api/avaliacoes", {"aluno_id": aid, "inicio": "2026-10-07T10:00", "professor": "carla"})
    p = api.aluno("Parou", "41999990002")
    api.msg("41999990002", "parar")
    api.post("/api/avaliacoes", {"aluno_id": p, "inicio": "2026-10-07T11:00", "professor": "carla"})
    assert api.rodar("2026-10-06T09:59")["enviadas"] == 0       # 09:59 + 24 h < 07/10 10:00
    assert api.rodar("2026-10-06T10:00")["enviadas"] == 1       # 10:00 + 24 h = 07/10 10:00 (inclusive)
    [m] = api.saida("avaliacao")
    assert m["telefone"] == "+5541999990001" and "07/10" in m["texto"] and "10:00" in m["texto"] and "Carla" in m["texto"]
    assert api.rodar("2026-10-06T12:00")["enviadas"] == 0
    assert api.saida() == [m]                                   # quem disse PARAR não ganhou mensagem
