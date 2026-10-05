"""Seções 14 e 15: direitos do titular (LGPD) e exportação para o Painel de Recuperação do Raio-X (pacote `servicos`)."""
import json
import subprocess

from conftest import RAIZ, Servidor, norm

# ids de `entradas` em raio-x-margem/setores/servicos.js (copiados em 05/10/2026); `valores` só pode usar estes
IDS_SERVICOS = {
    "faturamento", "atendimentos_mes", "ticket_medio", "margem_contrib_pct",
    "falta_pct", "falta_meta_pct", "horas_disponiveis_mes", "ocupacao_pct", "ocupacao_meta_pct", "receita_hora",
    "clientes_novos_mes", "retorno_atual_pct", "retorno_meta_pct", "atendimentos_mes_recorrente",
    "pct_com_adicional_atual", "pct_com_adicional_meta", "valor_adicional", "margem_adicional_pct",
    "receita_plataforma", "comissao_plataforma_pct", "custo_proprio_pct", "recorrente_plataforma_pct",
    "fat_cartao", "mdr_atual_pct", "mdr_referencia_pct", "valor_antecipado", "custo_antecipacao_pct", "juros_multas_mes",
    "horas_agenda_manual_semana", "custo_hora", "gasto_anuncios_mes", "anuncio_para_clientes_pct",
}
# vagas de outubro/2026 na grade do fixture (sem o feriado 12/10, segunda):
# seg 07:00 funcional 4 × 3 dias (5, 19, 26) = 12; ter 3 × 4 = 12; qua pilates 2 × 4 = 8; qua spinning 2 × 4 = 8; sex 4 × 5 = 20
VAGAS_OUT = 60


def test_dados_e_exclusao(api):
    tel = "41999990001"
    aid = api.ativo("Maria Silva", tel, marketing=True)
    outro = api.ativo("Outro", "41999990002")
    _, r1 = api.reserva(aid, "pil-qua-9", "2026-10-07")
    _, r2 = api.reserva(aid, "func-sex-18", "2026-10-09")
    api.post(f"/api/reservas/{r2['id']}/presenca", {"compareceu": True})
    api.post("/api/espera", {"aluno_id": outro, "aula_id": "pil-qua-9", "data": "2026-10-07"})
    cod = api.codigo(aid)
    api.checkin(cod)
    _, av = api.post("/api/avaliacoes", {"aluno_id": aid, "inicio": "2026-10-07T10:00"})
    api.post(f"/api/avaliacoes/{av['id']}/resultado", {"peso_kg": 70, "altura_cm": 165})
    api.put(f"/api/alunos/{aid}/ficha", {"treinos": [{"nome": "A", "itens": [{"exercicio": "prancha", "series": 3, "repeticoes": 30}]}]})
    api.msg(tel, "tem estacionamento")
    st, d = api.get(f"/api/alunos/{aid}/dados")
    assert st == 200
    assert d["aluno"]["nome"] == "Maria Silva" and d["aluno"]["telefone"] == "+5541999990001" and d["aluno"]["codigo"] == cod
    assert {x["id"] for x in d["reservas"]} == {r1["id"], r2["id"]} and len(d["matriculas"]) == 1 and len(d["checkins"]) == 1
    assert d["avaliacoes"][0]["resultado"]["peso_kg"] == 70 and d["ficha"]["treinos"][0]["nome"] == "A"
    assert {"entrada", "saida"} <= {m["direcao"] for m in d["mensagens"]}
    assert any("estacionamento" in m["texto"] for m in d["mensagens"])

    assert api.delete(f"/api/alunos/{aid}")[0] == 204
    st, d = api.get(f"/api/alunos/{aid}/dados")
    assert st == 200
    assert d["aluno"]["nome"] == "removido" and d["aluno"]["telefone"] is None and d["aluno"]["codigo"] is None
    assert {x["id"]: x["status"] for x in d["reservas"]} == {r1["id"]: "cancelada", r2["id"]: "presente"}
    assert d["avaliacoes"][0]["resultado"] is None and d["ficha"] is None and len(d["checkins"]) == 1
    assert d["mensagens"] and all(m["texto"] == "" for m in d["mensagens"])
    assert api.saida("espera") == []                               # a vaga abriu sem disparar a lista de espera
    assert api.ocorrencia("2026-10-07", "pil-qua-9")["livres"] == 2
    assert api.checkin(cod)[0] == 404                                # código antigo não vale mais
    assert api.get("/api/raiox?mes=2026-10")[1]["valores"]["atendimentos_mes"] == 1
    assert "nome" in norm(api.msg(tel, "quero reservar"))            # telefone virou desconhecido


def montar_mes(dados):
    """Setembro: dois alunos com plano vencendo em outubro (um renova). Outubro: o cenário medido."""
    s = Servidor(dados, agora="2026-09-10T09:00")
    api = s.subir()
    p6 = api.ativo("Seis", "41900000006")                            # mensal 10/09 → 09/10
    p7 = api.ativo("Sete", "41900000007", inicio="2026-09-12")       # mensal 12/09 → 11/10
    s.parar()

    s = Servidor(dados)  # agora = 06/10/2026 09:00
    api = s.subir()
    p1, p2, p3, p4, p5 = (api.ativo(n, f"4190000000{i}") for i, n in enumerate(["Um", "Dois", "Tres", "Quatro", "Cinco"], 1))
    st, m = api.matricula(p6, "mensal", inicio="2026-10-10")         # renovação dentro de [09/09, 08/11] → conta no retorno
    assert st == 201, m
    p8 = api.ativo("Oito", "41900000008")
    [m8] = api.get(f"/api/alunos/{p8}/matriculas")[1]["matriculas"]
    api.post(f"/api/matriculas/{m8['id']}/cancelar")                 # cancelamento em outubro

    def marca(pid, aula, data, compareceu=None):
        st, r = api.reserva(pid, aula, data)
        assert st == 201, (aula, data, r)
        if compareceu is not None:
            api.post(f"/api/reservas/{r['id']}/presenca", {"compareceu": compareceu})
        return r

    marca(p1, "pil-qua-9", "2026-10-07", True)      # presente
    marca(p2, "spin-qua-19", "2026-10-07", False)   # falta
    marca(p3, "func-sex-18", "2026-10-09", True)    # presente
    marca(p4, "spin-ter-7", "2026-10-13")           # reservada (ativa)
    c = marca(p5, "func-sex-18", "2026-10-09")      # cancelada: não conta
    api.post(f"/api/reservas/{c['id']}/cancelar")
    api.checkin(api.codigo(p1))
    api.checkin(api.codigo(p2))
    return s, api


def test_raiox_numeros_do_mes(dados):
    s, api = montar_mes(dados)
    try:
        st, r = api.get("/api/raiox?mes=2026-10")
        assert st == 200 and r["pacote"] == "servicos" and r["mes"] == "2026-10"
        v = r["valores"]
        assert set(v) <= IDS_SERVICOS, set(v) - IDS_SERVICOS
        assert v["atendimentos_mes"] == 2                            # check-ins de p1 e p2
        assert v["falta_pct"] == 33.3                                # 1 falta ÷ (2 presentes + 1 falta)
        assert abs(v["ocupacao_pct"] - 4 / VAGAS_OUT * 100) <= 0.06  # 4 ativas ÷ 60 = 6,7
        assert v["clientes_novos_mes"] == 6                          # p1..p5 e p8 (primeira matrícula em outubro)
        assert v["retorno_atual_pct"] == 50.0                        # fins em out: p6 (renovou) e p7 (não)
        assert abs(v["atendimentos_mes_recorrente"] - 2 / 6) <= 0.06 # 2 check-ins ÷ 6 ativos em 31/10 (p1..p5, p6 novo)
        assert r["indicadores"]["alunos_ativos"] == 6 and r["indicadores"]["cancelamentos_mes"] == 1
        st, s9 = api.get("/api/raiox?mes=2026-09")
        v9 = s9["valores"]
        assert (v9["atendimentos_mes"], v9["clientes_novos_mes"], v9["falta_pct"], v9["ocupacao_pct"], v9["retorno_atual_pct"]) == (0, 2, 0, 0, 0)
        assert s9["indicadores"]["alunos_ativos"] == 2               # p6 e p7 ativos em 30/09
    finally:
        s.parar()


def test_cli_grava_mes_no_acompanhamento_do_painel(dados, tmp_path):
    s, _ = montar_mes(dados)
    s.parar()
    arq = tmp_path / "acompanhamento.json"
    arq.write_text(json.dumps({
        "tipo": "acompanhamento", "pacote": "servicos", "cliente": "Academia Movimento",
        "base": {"data": "2026-09-01", "valores": {"falta_pct": 18, "ticket_medio": 150, "atendimentos_mes": 400}},
        "meses": [],
    }))
    cmd = [str(RAIZ / "atende"), "raiox", "--dados", str(dados), "--mes", "2026-10", "--acompanhamento", str(arq)]
    for _ in range(2):  # rodar duas vezes substitui o mês, não duplica
        assert subprocess.run(cmd, cwd=RAIZ, capture_output=True, timeout=30).returncode == 0
    acomp = json.loads(arq.read_text())
    assert acomp["tipo"] == "acompanhamento" and acomp["base"]["valores"]["falta_pct"] == 18
    [m] = acomp["meses"]
    assert m["mes"] == "2026-10" and m["obs"] == "atende-academia"
    assert m["valores"]["ticket_medio"] == 150          # mesclado da base
    assert m["valores"]["falta_pct"] == 33.3            # medido
    assert m["valores"]["atendimentos_mes"] == 2
    assert "alunos_ativos" not in m["valores"] and "indicadores" not in m
    assert set(m["valores"]) <= IDS_SERVICOS
