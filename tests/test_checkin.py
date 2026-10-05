"""Seção 5: check-in por código e pelo chat, frequência, reativação após inatividade. Agora = ter 06/10/2026 09:00."""
from conftest import Servidor, norm


def test_checkin_por_codigo_e_listagem(api):
    aid = api.ativo()
    cod = api.codigo(aid)
    st, r = api.checkin(cod)
    assert st == 201, r
    assert (r["aluno_id"], r["nome"], r["quando"]) == (aid, "Maria Silva", "2026-10-06T09:00")
    st, r2 = api.checkin(cod)                             # mesmo dia: devolve o mesmo
    assert st == 200 and r2["id"] == r["id"] and r2["quando"] == r["quando"]
    st, lista = api.get("/api/checkins?de=2026-10-06&ate=2026-10-06")
    assert st == 200 and [c["id"] for c in lista["checkins"]] == [r["id"]]
    assert len(api.get(f"/api/checkins?aluno_id={aid}")[1]["checkins"]) == 1
    assert api.get("/api/checkins?de=2026-10-07&ate=2026-10-07")[1]["checkins"] == []


def test_checkin_codigo_inexistente_404(api):
    assert api.checkin("000000")[0] == 404
    assert api.post("/api/checkins", {})[0] == 400


def test_checkin_sem_matricula_ativa_422_motivos(api):
    a1 = api.aluno("Sem", "41999990001")
    st, r = api.checkin(api.codigo(a1))
    assert (st, r["motivo"]) == (422, "sem_matricula")
    a2 = api.ativo("Vencida", "41999990002", inicio="2026-08-01")
    assert api.checkin(api.codigo(a2))[1]["motivo"] == "matricula_vencida"
    a3 = api.aluno("Trancada", "41999990003")
    _, m = api.matricula(a3, "mensal")
    api.post(f"/api/matriculas/{m['id']}/trancar")
    assert api.checkin(api.codigo(a3))[1]["motivo"] == "matricula_trancada"
    api.post(f"/api/matriculas/{m['id']}/destrancar")
    assert api.checkin(api.codigo(a3))[0] == 201


def test_checkin_pelo_chat(api):
    aid = api.ativo("Maria", "41988887777")
    r = norm(api.msg("41988887777", "cheguei!"))
    assert "check-in" in r and "bom treino" in r
    assert [c["aluno_id"] for c in api.get("/api/checkins?de=2026-10-06&ate=2026-10-06")[1]["checkins"]] == [aid]
    api.aluno("Sem plano", "41988880000")
    r = norm(api.msg("41988880000", "check-in"))
    assert "plano" in r and "recepcao" in r
    assert "nome" in norm(api.msg("41977776666", "fazer check in"))     # desconhecido: pede o nome
    r = norm(api.msg("41977776666", "Pedro Lima"))
    assert "plano" in r and "recepcao" in r
    assert [a["nome"] for a in api.get("/api/alunos?busca=pedro")[1]["alunos"]] == ["Pedro Lima"]


def test_reativacao_apos_inatividade(dados):
    s = Servidor(dados, agora="2026-09-22T10:00")
    api = s.subir()
    a1 = api.ativo("Um", "41999990001", plano="trimestral", inicio="2026-09-01", marketing=True)   # fim 29/11
    a2 = api.ativo("Dois", "41999990002", plano="trimestral", inicio="2026-09-20", marketing=True) # fim 18/12, nunca fez check-in
    a3 = api.ativo("Tres", "41999990003", plano="trimestral", inicio="2026-09-01", marketing=False)
    a4 = api.ativo("Quatro", "41999990004", plano="trimestral", inicio="2026-09-01", marketing=True)
    assert api.checkin(api.codigo(a1))[0] == 201
    assert api.checkin(api.codigo(a3))[0] == 201
    cod1, cod4 = api.codigo(a1), api.codigo(a4)
    s.parar()
    s2 = Servidor(dados, agora="2026-09-23T10:00")
    api = s2.subir()
    assert api.checkin(cod4)[0] == 201
    s2.parar()
    s3 = Servidor(dados)                                   # 06/10: a1 14 dias (conta), a2 16 dias desde o início,
    api = s3.subir()                                       # a3 sem consentimento, a4 13 dias (não conta)
    assert api.rodar()["enviadas"] == 2
    msgs = api.saida("reativacao")
    assert sorted(m["aluno_id"] for m in msgs) == [a1, a2]
    assert all("treinar" in norm(m["texto"]) for m in msgs)
    assert api.rodar()["enviadas"] == 0                    # uma por período de inatividade
    assert api.checkin(cod1)[0] == 201                     # a1 voltou em 06/10
    assert api.rodar("2026-10-19T09:00")["enviadas"] == 1  # a4: 19/10 − 23/09 = 26 dias; a1: 13 dias; a2: já avisado
    assert api.saida("reativacao")[-1]["aluno_id"] == a4
    assert api.rodar("2026-10-20T09:00")["enviadas"] == 1  # a1: 20/10 − 06/10 = 14 dias → avisa de novo
    assert api.saida("reativacao")[-1]["aluno_id"] == a1
    s3.parar()
