"""Seção 11: FAQ, não entendi, humano, alerta de saúde, aulas, reserva e cancelamento pelo chat, PARAR. Agora = ter 06/10/2026 09:00."""
from conftest import norm

TEL = "41988887777"
TEL_N = "+5541988887777"


def fila(api):
    st, r = api.get("/api/atendimento-humano")
    assert st == 200
    return r["fila"]


def test_faq_responde_exatamente(api):
    assert api.msg(TEL, "Oi, qual o horario de funcionamento?") == "Segunda a sexta das 6h às 22h, sábado das 8h às 12h."
    assert api.msg(TEL, "Onde fica a academia de vocês?") == "Rua das Palmeiras, 200, Água Verde, Curitiba."
    assert api.msg(TEL, "tem estacionamento aí?") == "Temos estacionamento próprio para 20 carros, sem custo."


def test_nao_entendi_humano_e_atendente(api):
    r = norm(api.msg(TEL, "vocês vendem whey?"))
    assert "nao entendi" in r and "atendente" in r
    assert fila(api) == []
    api.msg(TEL, "e creatina?")
    f = fila(api)
    assert len(f) == 1 and f[0]["telefone"] == TEL_N and f[0]["prioridade"] == "normal" and f[0]["status"] == "aberto"
    assert "atendente" in norm(api.msg("41977776666", "quero falar com um atendente"))
    assert [x["telefone"] for x in fila(api)] == [TEL_N, "+5541977776666"]


def test_alerta_de_saude_prioridade_alta(api):
    api.ativo("Maria", TEL)
    r = norm(api.msg(TEL, "quero reservar aula mas estou com dor no peito"))
    assert "pare" in r and "192" in r and "professor" in r
    f = fila(api)
    assert len(f) == 1 and f[0]["prioridade"] == "alta" and f[0]["telefone"] == TEL_N
    assert api.get("/api/reservas?data=2026-10-07")[1]["reservas"] == []
    api.msg("41977776666", "machuquei o joelho na aula")
    assert [x["prioridade"] for x in fila(api)] == ["alta", "alta"]


def test_aulas_pelo_chat(api):
    api.ativo("Maria", TEL)
    r = api.msg(TEL, "quais aulas tem?")
    assert "07/10 09:00 Pilates com Carla — 2 vagas" in r and "07/10 19:00 Spinning com Diego — 2 vagas" in r
    assert "06/10 07:00" not in r                      # a de hoje já passou
    assert "09/10" not in r                            # só hoje e amanhã


def test_reserva_pelo_chat_com_plano(api):
    aid = api.ativo("Maria", TEL)
    r = api.msg(TEL, "quero reservar uma aula")          # aluno conhecido: vai direto à lista
    assert "1) 07/10 09:00 Pilates com Carla" in r and "2) 07/10 19:00 Spinning com Diego" in r
    assert "3) 09/10 18:00 Funcional com Diego" in r and "4) 13/10 07:00 Spinning com Diego" in r and "5)" not in r
    assert "1) 07/10 09:00 Pilates com Carla" in api.msg(TEL, "9")     # número inválido: repete
    r = norm(api.msg(TEL, "1"))
    assert "reservad" in r and "07/10" in r and "09:00" in r
    [x] = api.get("/api/reservas?data=2026-10-07")[1]["reservas"]
    assert (x["aluno_id"], x["aula_id"], x["status"]) == (aid, "pil-qua-9", "reservada")
    outro = api.ativo("Outro", "41999990009")
    api.reserva(outro, "pil-qua-9", "2026-10-07")                       # lotou
    r = api.msg(TEL, "reservar")
    assert "1) 07/10 19:00 Spinning com Diego" in r and "Pilates" not in r


def test_reserva_pelo_chat_sem_plano_e_desconhecido(api):
    assert "nome" in norm(api.msg(TEL, "quero reservar uma aula"))
    r = norm(api.msg(TEL, "Pedro Lima"))
    assert "plano" in r and "recepcao" in r
    [a] = api.get("/api/alunos?busca=pedro")[1]["alunos"]
    assert a["nome"] == "Pedro Lima" and a["telefone"] == TEL_N and a["consentimento_marketing"] is False
    r = norm(api.msg(TEL, "quero marcar spinning"))       # já cadastrado: não pede nome de novo, continua sem plano
    assert "plano" in r and "recepcao" in r
    assert len(api.get("/api/alunos?busca=pedro")[1]["alunos"]) == 1
    assert api.get("/api/reservas?data=2026-10-07")[1]["reservas"] == []


def test_cancelar_reserva_pelo_chat(api):
    aid = api.ativo("Maria", TEL)
    _, r1 = api.reserva(aid, "pil-qua-9", "2026-10-07")
    _, r2 = api.reserva(aid, "func-sex-18", "2026-10-09")
    r = api.msg(TEL, "quero cancelar")
    assert "1) 07/10 09:00 Pilates" in r and "2) 09/10 18:00 Funcional" in r
    assert "cancelad" in norm(api.msg(TEL, "2"))
    status = {x["id"]: x["status"] for x in api.get(f"/api/reservas?aluno_id={aid}")[1]["reservas"]}
    assert status == {r1["id"]: "reservada", r2["id"]: "cancelada"}
    r = api.msg(TEL, "desmarcar")
    assert "1) 07/10 09:00 Pilates" in r and "Funcional" not in r
    api.ativo("Sem reserva", "41977776666")
    assert "nenhuma reserva" in norm(api.msg("41977776666", "cancelar"))


def test_cancelar_sai_do_fluxo_e_parar_bloqueia(api):
    aid = api.ativo("Maria", TEL, inicio="2026-09-10")        # fim 09/10: aviso de vencimento pendente
    assert "1) 07/10 09:00" in api.msg(TEL, "reservar")
    assert "ok" in norm(api.msg(TEL, "cancelar"))
    assert api.msg(TEL, "tem estacionamento") == "Temos estacionamento próprio para 20 carros, sem custo."
    assert api.get("/api/reservas?data=2026-10-07")[1]["reservas"] == []
    assert "nao vai mais receber" in norm(api.msg(TEL, "PARAR"))
    assert api.rodar()["enviadas"] == 0
    assert api.saida() == []
    assert api.get(f"/api/alunos/{aid}/dados")[1]["aluno"]["nao_contatar"] is True
    assert api.msg(TEL, "tem estacionamento") == "Temos estacionamento próprio para 20 carros, sem custo."   # o bot ainda responde
