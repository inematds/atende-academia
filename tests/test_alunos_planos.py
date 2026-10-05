"""Seção 3: alunos, planos, matrículas (vigência, status, pagamento manual, aviso de vencimento). Agora = ter 06/10/2026 09:00."""
import re

from conftest import norm


def test_telefone_normalizado_duplicado_e_codigo(api):
    st, r = api.post("/api/alunos", {"nome": "A", "telefone": "(41) 99999-0001"})
    assert st == 201 and re.fullmatch(r"\d{4,8}", r["codigo"]), r
    st2, r2 = api.post("/api/alunos", {"nome": "A", "telefone": "+55 41 99999 0001"})
    assert st2 == 200 and r2["id"] == r["id"] and r2["codigo"] == r["codigo"]
    st3, r3 = api.post("/api/alunos", {"nome": "B", "telefone": "41 3333-4444"})
    assert st3 == 201 and r3["id"] != r["id"] and r3["codigo"] != r["codigo"]
    st, d = api.get(f"/api/alunos/{r3['id']}/dados")
    assert d["aluno"]["telefone"] == "+554133334444" and d["aluno"]["codigo"] == r3["codigo"]
    st, lista = api.get(f"/api/alunos?busca={r['codigo']}")    # busca pelo código exato (pode casar dígitos de telefone também)
    assert st == 200 and r["id"] in [a["id"] for a in lista["alunos"]]
    for ruim in ("123", "abc", "+55 41 9999"):
        assert api.post("/api/alunos", {"nome": "C", "telefone": ruim})[0] == 400, ruim


def test_matricula_calcula_fim_e_status(api):
    aid = api.aluno()
    st, m = api.matricula(aid, "mensal")
    assert st == 201, m
    # vigência inclusiva: 06/10 + 30 dias − 1 = 04/11
    assert (m["inicio"], m["fim"], m["status"], m["pagamento"], m["aulas_restantes"]) == \
        ("2026-10-06", "2026-11-04", "ativa", "pendente", None)
    st, a = api.matricula(aid, "anual", inicio="2026-10-06")
    assert st == 201 and a["fim"] == "2027-10-05"          # 06/10/2026 + 364 = 05/10/2027
    st, lista = api.get(f"/api/alunos/{aid}/matriculas")
    assert [x["id"] for x in lista["matriculas"]] == [m["id"], a["id"]]
    assert api.matricula(9999, "mensal")[0] == 404
    assert api.matricula(aid, "xyz")[0] == 404


def test_matricula_vencida_trancada_cancelada(api):
    aid = api.aluno()
    st, m1 = api.matricula(aid, "mensal", inicio="2026-08-01")   # fim 30/08 < hoje → vencida
    assert st == 201 and m1["fim"] == "2026-08-30" and m1["status"] == "vencida"
    st, m2 = api.matricula(aid, "mensal")
    assert api.post(f"/api/matriculas/{m2['id']}/trancar")[1]["status"] == "trancada"
    st, r = api.post(f"/api/matriculas/{m2['id']}/destrancar")
    assert st == 200 and r["status"] == "ativa" and r["fim"] == "2026-11-04"   # trancar não estende a vigência
    st, r = api.post(f"/api/matriculas/{m2['id']}/cancelar")
    assert st == 200 and r["status"] == "cancelada"
    assert api.post(f"/api/matriculas/{m2['id']}/trancar")[0] == 409
    assert api.post(f"/api/matriculas/{m2['id']}/pagamento", {"pago": True})[0] == 409
    assert api.post("/api/matriculas/9999/cancelar")[0] == 404


def test_pagamento_manual(api):
    aid = api.aluno()
    _, m = api.matricula(aid, "trimestral")
    st, r = api.post(f"/api/matriculas/{m['id']}/pagamento", {"pago": True})
    assert st == 200 and r["pagamento"] == "pago" and r["id"] == m["id"]
    assert api.post(f"/api/matriculas/{m['id']}/pagamento", {"pago": False})[1]["pagamento"] == "pendente"
    assert api.post(f"/api/matriculas/{m['id']}/pagamento", {})[0] == 400


def test_lembrete_vencimento_uma_vez_e_fronteira(api):
    p1 = api.aluno("Maria", "41999990001")
    _, m1 = api.matricula(p1, "mensal", inicio="2026-09-10")      # fim 09/10; aviso a partir de 09/10 − 5 = 04/10
    p2 = api.aluno("Cancelou", "41999990002")
    _, m2 = api.matricula(p2, "mensal", inicio="2026-09-10")
    api.post(f"/api/matriculas/{m2['id']}/cancelar")
    p3 = api.aluno("Parou", "41999990003")
    api.matricula(p3, "mensal", inicio="2026-09-10")
    api.msg("41999990003", "parar")
    p4 = api.aluno("Longe", "41999990004")
    api.matricula(p4, "mensal")                                    # fim 04/11: fora da janela
    assert api.rodar("2026-10-03T09:00")["enviadas"] == 0
    r = api.rodar("2026-10-04T09:00")
    assert r["enviadas"] == 1
    [m] = api.saida("vencimento")
    assert m["telefone"] == "+5541999990001" and m["aluno_id"] == p1 and m["referencia_id"] == m1["id"]
    assert "mensal" in norm(m["texto"]) and "09/10" in m["texto"]
    assert api.rodar()["enviadas"] == 0                            # 06/10: já avisada
    assert api.rodar("2026-10-09T23:00")["enviadas"] == 0
    assert [x["aluno_id"] for x in api.saida("vencimento")] == [p1]


def test_meu_plano_pelo_chat(api):
    api.ativo("Ativa", "41999990001", inicio="2026-09-10")        # fim 09/10
    r = api.msg("41999990001", "qual é o meu plano?")
    assert "Mensal" in r and "09/10" in r and "ativ" in norm(r)
    r = api.msg("41999990001", "quando vence minha mensalidade")
    assert "09/10" in r
    api.ativo("Vencida", "41999990002", inicio="2026-08-01")      # fim 30/08
    r = api.msg("41999990002", "meu plano")
    assert "Mensal" in r and "30/08" in r and "vencid" in norm(r)
    api.aluno("Sem", "41999990003")
    r = norm(api.msg("41999990003", "qual meu plano"))
    assert "plano" in r and "recepcao" in r


def test_alunos_busca_e_edicao(api):
    p1 = api.aluno("José Antônio Souza", "41999990001")
    p2 = api.aluno("Maria Lima", "41999990002")
    st, r = api.get("/api/alunos?busca=antonio")
    assert st == 200 and [p["id"] for p in r["alunos"]] == [p1]
    st, r = api.get("/api/alunos?busca=990002")
    assert [p["id"] for p in r["alunos"]] == [p2]
    assert [p["id"] for p in api.get("/api/alunos")[1]["alunos"]] == [p1, p2]
    st, r = api.put(f"/api/alunos/{p2}", {"email": "maria@exemplo.com", "nascimento": "1980-05-02", "consentimento_marketing": True})
    assert st == 200 and r["email"] == "maria@exemplo.com" and r["consentimento_marketing"] is True
    assert api.put(f"/api/alunos/{p2}", {"telefone": "41999990001"})[0] == 409
    assert api.put(f"/api/alunos/{p2}", {"telefone": "12"})[0] == 400
    assert api.put("/api/alunos/9999", {"nome": "X"})[0] == 404


def test_matricula_avulsa_tem_creditos(api):
    aid = api.aluno()
    st, m = api.matricula(aid, "avulso5")
    assert st == 201 and m["aulas_restantes"] == 5 and m["fim"] == "2026-12-04"   # 06/10 + 60 − 1
    assert m["status"] == "ativa"


def test_plano_inativo_nao_aceita_matricula(api):
    st, r = api.delete("/api/planos/anual")
    assert st == 200 and r["ativo"] is False
    assert [p["id"] for p in api.get("/api/planos", token=None)[1]["planos"]] == ["mensal", "trimestral", "avulso5"]
    aid = api.aluno()
    assert api.matricula(aid, "anual")[0] == 422
    assert api.matricula(aid, "mensal")[0] == 201
