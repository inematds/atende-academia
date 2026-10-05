"""Seção 4: grade, ocorrências, reservas, cancelamento, espera, créditos, presença, ocorrência cancelada.
Agora = ter 06/10/2026 09:00. Grade do fixture: seg 07:00 funcional (4), ter 07:00 spinning (3),
qua 09:00 pilates (2), qua 19:00 spinning (2), sex 18:00 funcional (4). Feriado 12/10 (segunda)."""
import threading

from conftest import Servidor


def test_aulas_do_dia_ordem_e_campos(api):
    a = api.aulas("2026-10-07")
    assert [(x["aula_id"], x["inicio"]) for x in a] == [("pil-qua-9", "2026-10-07T09:00"), ("spin-qua-19", "2026-10-07T19:00")]
    p = a[0]
    assert (p["data"], p["fim"], p["modalidade"], p["professor"], p["sala"]) == ("2026-10-07", "2026-10-07T10:00", "Pilates", "Carla", "Sala 2")
    assert (p["vagas"], p["reservadas"], p["livres"], p["cancelada"]) == (2, 0, 2, False)
    # hoje: a aula das 07:00 já passou e mesmo assim aparece na listagem do dia
    assert [(x["aula_id"], x["inicio"]) for x in api.aulas("2026-10-06")] == [("spin-ter-7", "2026-10-06T07:00")]


def test_sem_aula_em_feriado_e_domingo_e_periodo(api):
    assert api.aulas("2026-10-12") == []     # feriado (segunda)
    assert api.aulas("2026-10-11") == []     # domingo
    assert [x["aula_id"] for x in api.aulas("2026-10-19")] == ["func-seg-7"]
    st, r = api.get("/api/aulas?de=2026-10-05&ate=2026-10-07")
    assert st == 200
    assert [x["inicio"] for x in r["aulas"]] == ["2026-10-05T07:00", "2026-10-06T07:00", "2026-10-07T09:00", "2026-10-07T19:00"]


def test_reservar_e_listar(api):
    aid = api.ativo()
    st, r = api.reserva(aid, "pil-qua-9", "2026-10-07")
    assert st == 201, r
    assert (r["aluno_id"], r["aula_id"], r["data"], r["inicio"], r["status"], r["aulas_restantes"]) == \
        (aid, "pil-qua-9", "2026-10-07", "2026-10-07T09:00", "reservada", None)
    o = api.ocorrencia("2026-10-07", "pil-qua-9")
    assert (o["reservadas"], o["livres"]) == (1, 1)
    st, lista = api.get("/api/reservas?data=2026-10-07")
    [x] = lista["reservas"]
    assert (x["id"], x["nome"], x["telefone"], x["modalidade"], x["status"]) == (r["id"], "Maria Silva", "+5541999990001", "Pilates", "reservada")
    assert len(api.get(f"/api/reservas?aluno_id={aid}")[1]["reservas"]) == 1
    assert api.get("/api/reservas?data=2026-10-08")[1]["reservas"] == []


def test_reserva_invalida_422_e_404(api):
    aid = api.ativo()
    for aula, data, motivo in [
        ("pil-qua-9", "2026-10-08", "sem_aula"),      # quinta: não é dia da aula
        ("func-seg-7", "2026-10-12", "sem_aula"),     # feriado
        ("spin-ter-7", "2026-10-06", "aula_passada"), # hoje 07:00 < agora 09:00
        ("spin-ter-7", "2026-10-20", "antecedencia"), # hoje + 14 > hoje + 7
    ]:
        st, r = api.reserva(aid, aula, data)
        assert (st, r.get("motivo")) == (422, motivo), (aula, data, r)
    assert api.reserva(aid, "spin-ter-7", "2026-10-13")[0] == 201   # hoje + 7 ainda vale (inclusive)
    assert api.reserva(aid, "xyz", "2026-10-07")[0] == 404
    assert api.reserva(9999, "pil-qua-9", "2026-10-07")[0] == 404


def test_reserva_sem_matricula_ativa_422_motivos(api):
    a1 = api.aluno("Sem", "41999990001")
    st, r = api.reserva(a1, "pil-qua-9", "2026-10-07")
    assert (st, r["motivo"]) == (422, "sem_matricula")
    a2 = api.ativo("Vencida", "41999990002", inicio="2026-08-01")   # fim 30/08
    assert api.reserva(a2, "pil-qua-9", "2026-10-07")[1]["motivo"] == "matricula_vencida"
    a3 = api.aluno("Trancada", "41999990003")
    _, m = api.matricula(a3, "mensal")
    api.post(f"/api/matriculas/{m['id']}/trancar")
    assert api.reserva(a3, "pil-qua-9", "2026-10-07")[1]["motivo"] == "matricula_trancada"
    a4 = api.ativo("Termina", "41999990004", inicio="2026-09-10")   # fim 09/10: cobre 07/10, não cobre 13/10
    assert api.reserva(a4, "pil-qua-9", "2026-10-07")[0] == 201
    assert api.reserva(a4, "spin-ter-7", "2026-10-13")[1]["motivo"] == "matricula_vencida"


def test_lotada_e_duplicada_409(api):
    a1 = api.ativo("Um", "41999990001")
    a2 = api.ativo("Dois", "41999990002")
    a3 = api.ativo("Tres", "41999990003")
    assert api.reserva(a1, "pil-qua-9", "2026-10-07")[0] == 201
    st, r = api.reserva(a1, "pil-qua-9", "2026-10-07")
    assert (st, r["motivo"]) == (409, "ja_reservada")
    assert api.reserva(a2, "pil-qua-9", "2026-10-07")[0] == 201
    st, r = api.reserva(a3, "pil-qua-9", "2026-10-07")
    assert (st, r["motivo"]) == (409, "lotada")
    assert api.ocorrencia("2026-10-07", "pil-qua-9")["livres"] == 0


def test_concorrencia_ultima_vaga(api):
    a0 = api.ativo("Zero", "41999990000")
    assert api.reserva(a0, "pil-qua-9", "2026-10-07")[0] == 201    # sobra 1 vaga
    alunos = [api.ativo(f"A{i}", f"4199999{i:04d}") for i in range(1, 11)]
    resultados = []

    def tenta(aid):
        resultados.append(api.reserva(aid, "pil-qua-9", "2026-10-07"))

    ts = [threading.Thread(target=tenta, args=(aid,)) for aid in alunos]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert sorted(st for st, _ in resultados) == [201] + [409] * 9
    assert all(r["motivo"] == "lotada" for st, r in resultados if st == 409)
    assert api.ocorrencia("2026-10-07", "pil-qua-9")["reservadas"] == 2


def test_cancelar_dentro_e_fora_do_prazo(dados):
    s = Servidor(dados)                                   # 06/10 09:00: 24 h antes da aula de 07/10 09:00
    api = s.subir()
    a1 = api.ativo("Um", "41999990001")
    a2 = api.ativo("Dois", "41999990002")
    a3 = api.ativo("Tres", "41999990003")
    _, r1 = api.reserva(a1, "pil-qua-9", "2026-10-07")
    _, r2 = api.reserva(a2, "pil-qua-9", "2026-10-07")
    st, r = api.post(f"/api/reservas/{r1['id']}/cancelar")
    assert st == 200 and r["status"] == "cancelada"
    assert api.ocorrencia("2026-10-07", "pil-qua-9")["livres"] == 1
    assert api.post(f"/api/reservas/{r1['id']}/cancelar")[0] == 409   # já cancelada
    s.parar()
    s2 = Servidor(dados, agora="2026-10-07T07:00")        # exatamente 2 h antes: ainda dentro do prazo
    api = s2.subir()
    assert api.post(f"/api/reservas/{r2['id']}/cancelar")[1]["status"] == "cancelada"
    st, r3 = api.reserva(a3, "pil-qua-9", "2026-10-07")
    assert st == 201
    s2.parar()
    s3 = Servidor(dados, agora="2026-10-07T07:30")        # 1 h 30 antes: fora do prazo
    api = s3.subir()
    st, r = api.post(f"/api/reservas/{r3['id']}/cancelar")
    assert st == 200 and r["status"] == "cancelada_tarde"
    assert api.ocorrencia("2026-10-07", "pil-qua-9")["livres"] == 2   # libera a vaga mesmo assim
    s3.parar()


def test_avulso_consome_e_devolve_credito(api):
    aid = api.ativo("Avulsa", "41999990001", plano="avulso5")
    st, r1 = api.reserva(aid, "pil-qua-9", "2026-10-07")
    assert st == 201 and r1["aulas_restantes"] == 4
    st, r2 = api.reserva(aid, "spin-qua-19", "2026-10-07")
    assert st == 201 and r2["aulas_restantes"] == 3
    assert api.post(f"/api/reservas/{r1['id']}/cancelar")[1]["status"] == "cancelada"   # dentro do prazo: devolve
    [m] = api.get(f"/api/alunos/{aid}/matriculas")[1]["matriculas"]
    assert m["aulas_restantes"] == 4
    api.post(f"/api/reservas/{r2['id']}/presenca", {"compareceu": False})               # falta: não devolve
    assert api.get(f"/api/alunos/{aid}/matriculas")[1]["matriculas"][0]["aulas_restantes"] == 4
    # plano de 1 aula criado pela equipe: zera e recusa
    assert api.post("/api/planos", {"id": "avulso1", "nome": "1 aula", "preco": 30, "vigencia_dias": 30, "aulas": 1})[0] == 201
    b = api.ativo("Uma", "41999990002", plano="avulso1")
    assert api.reserva(b, "func-sex-18", "2026-10-09")[1]["aulas_restantes"] == 0
    st, r = api.reserva(b, "spin-ter-7", "2026-10-13")
    assert (st, r["motivo"]) == (422, "sem_aulas")


def test_lista_de_espera_oferece_reserva_e_lotada(api):
    a1 = api.ativo("Um", "41999990001")
    a2 = api.ativo("Dois", "41999990002")
    a3 = api.ativo("Tres", "41999990003")
    a4 = api.ativo("Quatro", "41999990004")
    a5 = api.ativo("Cinco", "41999990005")
    a6 = api.ativo("Seis", "41999990006")
    _, r1 = api.reserva(a1, "pil-qua-9", "2026-10-07")
    _, r2 = api.reserva(a2, "pil-qua-9", "2026-10-07")
    for aid, aula in ((a3, "pil-qua-9"), (a4, "pil-qua-9"), (a5, "spin-qua-19")):
        assert api.post("/api/espera", {"aluno_id": aid, "aula_id": aula, "data": "2026-10-07"})[0] == 201
    assert api.post("/api/espera", {"aluno_id": a3, "aula_id": "xyz", "data": "2026-10-07"})[0] == 404
    api.post(f"/api/reservas/{r1['id']}/cancelar")
    ofertas = api.saida("espera")
    assert [m["telefone"] for m in ofertas] == ["+5541999990003"]
    assert "07/10" in ofertas[0]["texto"] and "09:00" in ofertas[0]["texto"] and "1" in ofertas[0]["texto"]
    st, e = api.get("/api/espera?data=2026-10-07")
    assert [(x["aluno_id"], x["status"]) for x in e["espera"]] == [(a3, "ofertado"), (a4, "pendente"), (a5, "pendente")]
    assert "reservad" in api.msg("41999990003", "1").lower()
    st, lista = api.get("/api/reservas?data=2026-10-07")
    ativas = [x["aluno_id"] for x in lista["reservas"] if x["status"] == "reservada"]
    assert ativas == [a2, a3]
    # abre outra vaga, oferece ao próximo, mas a recepção preenche antes da resposta
    api.post(f"/api/reservas/{r2['id']}/cancelar")
    assert [m["telefone"] for m in api.saida("espera")] == ["+5541999990003", "+5541999990004"]
    assert api.reserva(a6, "pil-qua-9", "2026-10-07")[0] == 201
    assert "lotada" in api.msg("41999990004", "sim").lower()


def test_presenca_manual_e_automatica(dados):
    s = Servidor(dados)
    api = s.subir()
    a1 = api.ativo("Faltou", "41999990001")
    a2 = api.ativo("Veio", "41999990002")
    _, r1 = api.reserva(a1, "pil-qua-9", "2026-10-07")
    _, r2 = api.reserva(a2, "pil-qua-9", "2026-10-07")
    _, r3 = api.reserva(a1, "spin-qua-19", "2026-10-07")
    cod2 = api.codigo(a2)
    s.parar()
    s2 = Servidor(dados, agora="2026-10-07T08:30")
    api = s2.subir()
    assert api.checkin(cod2)[0] == 201
    api.rodar("2026-10-07T09:30")                         # aula termina 10:00: ainda nada
    status = {x["id"]: x["status"] for x in api.get("/api/reservas?data=2026-10-07")[1]["reservas"]}
    assert status == {r1["id"]: "reservada", r2["id"]: "reservada", r3["id"]: "reservada"}
    r = api.rodar("2026-10-07T10:00")                     # fim ≤ agora: marca
    assert r["presencas"] == 2
    status = {x["id"]: x["status"] for x in api.get("/api/reservas?data=2026-10-07")[1]["reservas"]}
    assert status == {r1["id"]: "falta", r2["id"]: "presente", r3["id"]: "reservada"}
    assert api.rodar("2026-10-07T10:00")["presencas"] == 0
    st, x = api.post(f"/api/reservas/{r1['id']}/presenca", {"compareceu": True})   # a equipe corrige
    assert st == 200 and x["status"] == "presente"
    assert api.post(f"/api/reservas/{r1['id']}/presenca", {"compareceu": False})[1]["status"] == "falta"
    s2.parar()


def test_equipe_cancela_ocorrencia(api):
    a1 = api.ativo("Um", "41999990001")
    a2 = api.ativo("Avulsa", "41999990002", plano="avulso5")
    _, r1 = api.reserva(a1, "spin-qua-19", "2026-10-07")
    _, r2 = api.reserva(a2, "spin-qua-19", "2026-10-07")
    assert r2["aulas_restantes"] == 4
    st, r = api.post("/api/aulas/spin-qua-19/ocorrencias/2026-10-07/cancelar", {"motivo": "professor doente"})
    assert st == 200 and r["canceladas"] == 2
    status = {x["id"]: x["status"] for x in api.get("/api/reservas?data=2026-10-07")[1]["reservas"]}
    assert status == {r1["id"]: "cancelada_pela_academia", r2["id"]: "cancelada_pela_academia"}
    assert api.get(f"/api/alunos/{a2}/matriculas")[1]["matriculas"][0]["aulas_restantes"] == 5   # crédito devolvido
    avisos = api.saida("aula_cancelada")
    assert sorted(m["telefone"] for m in avisos) == ["+5541999990001", "+5541999990002"]
    assert all("07/10" in m["texto"] and "19:00" in m["texto"] and "Spinning" in m["texto"] for m in avisos)
    o = api.ocorrencia("2026-10-07", "spin-qua-19")
    assert o["cancelada"] is True and o["livres"] == 0
    st, r = api.reserva(a1, "spin-qua-19", "2026-10-07")
    assert (st, r["motivo"]) == (422, "sem_aula")
    assert api.post("/api/aulas/spin-qua-19/ocorrencias/2026-10-07/cancelar")[0] == 409
    assert api.post("/api/aulas/spin-qua-19/ocorrencias/2026-10-08/cancelar")[0] == 404
