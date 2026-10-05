"""Seção 13: campanha só com consentimento e trava mínima de publicidade."""
import pytest

CASOS = [
    # texto, violações esperadas (None = permitido)
    ("Resultado garantido em 30 dias!", {"promessa_resultado"}),
    ("Veja o antes e depois dos nossos alunos", {"antes_depois"}),
    ("Emagreça 100% garantido, veja o antes e depois", {"promessa_resultado", "antes_depois"}),
    ("Nova turma de pilates às quartas, 9h. Reserve pelo chat.", None),
]


@pytest.mark.parametrize("texto,esperado", CASOS, ids=[f"caso-{i}" for i in range(len(CASOS))])
def test_trava_de_publicidade(api, texto, esperado):
    api.aluno("Maria", "41999990001", marketing=True)
    st, r = api.post("/api/campanhas", {"texto": texto})
    if esperado is None:
        assert st == 200 and r["enviadas"] == 1, (st, r)
        [m] = api.saida("campanha")
        assert m["texto"] == texto and m["telefone"] == "+5541999990001"
    else:
        assert st == 422, (st, r)
        assert set(r["violacoes"]) == esperado
        assert api.saida("campanha") == []


def test_publico_so_com_consentimento_e_sem_parar(api):
    api.aluno("Com", "41999990001", marketing=True)
    api.aluno("Sem", "41999990002", marketing=False)
    api.aluno("Parou", "41999990003", marketing=True)
    api.msg("41999990003", "parar")
    st, r = api.post("/api/campanhas", {"texto": "Nova turma de funcional às sextas, 18h."})
    assert st == 200 and r["enviadas"] == 1
    assert [m["telefone"] for m in api.saida("campanha")] == ["+5541999990001"]
