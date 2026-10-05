"""Seções 6 e 7.3: biblioteca de exercícios, ficha do aluno, "meu treino de hoje", explicação pelo chat."""
from conftest import Servidor, norm

IDS = ["agachamento", "flexao", "prancha", "remada", "supino", "terra-bastao", "afundo", "elevacao-pelvica",
       "abdominal", "desenvolvimento", "puxada", "polichinelo"]

FICHA = {"treinos": [
    {"nome": "A", "itens": [{"exercicio": "agachamento", "series": 3, "repeticoes": 12, "carga": "20 kg", "descanso_s": 60},
                            {"exercicio": "prancha", "series": 3, "repeticoes": 30}]},
    {"nome": "B", "itens": [{"exercicio": "flexao", "series": 3, "repeticoes": 10}]},
]}


def test_biblioteca_lista_e_404(api):
    st, r = api.get("/api/exercicios", token=None)
    assert st == 200 and [e["id"] for e in r["exercicios"]] == IDS
    st, e = api.get("/api/exercicios/prancha", token=None)
    assert st == 200
    assert (e["nome"], e["grupo"], len(e["passos"]), e["svg"], e["ativo"]) == ("Prancha", "core", 3, True, True)
    assert "plank" in e["apelidos"] and e["erros_comuns"] and e["cuidados"]
    assert api.get("/api/exercicios/xyz", token=None)[0] == 404


def test_ficha_montar_e_ler(api):
    aid = api.aluno()
    st, r = api.put(f"/api/alunos/{aid}/ficha", FICHA)
    assert st == 200 and [t["nome"] for t in r["treinos"]] == ["A", "B"]
    st, r = api.get(f"/api/alunos/{aid}/ficha")
    assert st == 200 and r["treinos"][0]["itens"][0]["carga"] == "20 kg" and r["treinos"][1]["itens"][0]["series"] == 3
    assert api.put(f"/api/alunos/{aid}/ficha", {"treinos": [{"nome": "C", "itens": [{"exercicio": "xyz", "series": 3, "repeticoes": 10}]}]})[0] == 422
    assert api.put("/api/alunos/9999/ficha", FICHA)[0] == 404
    assert api.get("/api/alunos/9999/ficha")[0] == 404
    assert api.delete(f"/api/alunos/{aid}/ficha")[0] == 204
    assert api.get(f"/api/alunos/{aid}/ficha")[0] == 404


def test_meu_treino_pelo_chat_rotaciona(dados):
    s = Servidor(dados, agora="2026-10-05T10:00")
    api = s.subir()
    aid = api.ativo("Maria", "41988887777", inicio="2026-10-01")
    api.put(f"/api/alunos/{aid}/ficha", FICHA)
    cod = api.codigo(aid)
    r = api.msg("41988887777", "meu treino de hoje")
    assert r.splitlines()[0] == "Treino A"
    assert "- Agachamento: 3x12, 20 kg, descanso 60 s" in r and "- Prancha: 3x30" in r
    assert "explica" in norm(r)
    api.checkin(cod)
    assert api.msg("41988887777", "qual meu treino?").splitlines()[0] == "Treino A"   # check-in de hoje não conta
    s.parar()
    s2 = Servidor(dados)                                   # 06/10: 1 check-in em dia anterior → B
    api = s2.subir()
    r = api.msg("41988887777", "meu treino")
    assert r.splitlines()[0] == "Treino B" and "- Flexão de braço: 3x10" in r
    api.checkin(cod)
    s2.parar()
    s3 = Servidor(dados, agora="2026-10-07T10:00")        # 2 check-ins anteriores → 2 mod 2 = 0 → A
    api = s3.subir()
    assert api.msg("41988887777", "treino de hoje").splitlines()[0] == "Treino A"
    s3.parar()


def test_meu_treino_sem_ficha_ou_sem_plano(api):
    api.ativo("Com plano", "41999990001")
    r = norm(api.msg("41999990001", "meu treino"))
    assert "ficha" in r and "professor" in r
    api.aluno("Sem plano", "41999990002")
    r = norm(api.msg("41999990002", "qual a minha ficha"))
    assert "plano" in r and "recepcao" in r


def test_explicar_exercicio_pelo_chat(api):
    r = api.msg("41988887777", "como faço a prancha?")
    linhas = r.splitlines()
    assert linhas[0] == "Prancha"
    assert "1. Antebraços no chão, cotovelos abaixo dos ombros." in r and "2. " in r and "3. " in r
    assert "Cuidado: Dor na lombar: pare e avise o professor." in r
    assert linhas[-1] == "Veja a animação: /exercicios/prancha"
    assert api.msg("41988887777", "me mostra o push-up").splitlines()[0] == "Flexão de braço"
    assert api.msg("41988887777", "explica o levantamento terra").splitlines()[0] == "Levantamento terra com bastão"
    assert api.get("/api/atendimento-humano")[1]["fila"] == []


def test_exercicio_novo_sem_svg(api):
    novo = {"id": "rosca", "nome": "Rosca direta", "apelidos": ["rosca", "biceps"], "grupo": "bracos",
            "passos": ["Segure os halteres com as palmas para a frente.", "Dobre os cotovelos sem mover os ombros."],
            "cuidados": ["Não balance o tronco."]}
    st, r = api.post("/api/exercicios", novo)
    assert st == 201, r
    assert api.post("/api/exercicios", novo)[0] == 409
    assert api.post("/api/exercicios", {"id": "vazio", "nome": "Vazio", "passos": []})[0] == 422
    lista = api.get("/api/exercicios", token=None)[1]["exercicios"]
    assert lista[-1]["id"] == "rosca" and lista[-1]["svg"] is False
    r = api.msg("41988887777", "como faz a rosca?")
    assert r.splitlines()[0] == "Rosca direta" and "1. Segure os halteres" in r and "Veja a animação" not in r
    st, html = api.get("/exercicios/rosca", token=None)
    assert st == 200 and "Rosca direta" in html and ".svg" not in html
    assert api.get("/exercicios/rosca.svg", token=None)[0] == 404
