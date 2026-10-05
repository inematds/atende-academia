"""Seções 7.1 e 7.2: um SVG animado por exercício do catálogo de exemplo (checagem sem navegador) e as rotas de arquivo."""
import json
import re
import xml.etree.ElementTree as ET

import pytest

from conftest import RAIZ, Servidor

PASTA = RAIZ / "web" / "exercicios"
IDS = ["agachamento", "flexao", "prancha", "remada", "supino", "terra-bastao", "afundo", "elevacao-pelvica",
       "abdominal", "desenvolvimento", "puxada", "polichinelo"]
SVG_NS = "http://www.w3.org/2000/svg"


@pytest.mark.parametrize("ex", IDS)
def test_svg_do_exercicio(ex):
    p = PASTA / f"{ex}.svg"
    assert p.exists(), f"falta {p.relative_to(RAIZ)}"
    texto = p.read_text(encoding="utf-8")
    assert len(texto.encode("utf-8")) <= 61440, "SVG maior que 60 KB"
    raiz = ET.fromstring(texto)                                   # XML válido
    assert raiz.tag == f"{{{SVG_NS}}}svg" and raiz.get("viewBox")
    titulo = raiz.find(f"{{{SVG_NS}}}title")
    assert titulo is not None and (titulo.text or "").strip(), "<title> em português"
    smil = re.search(r"<animate(Transform|Motion)?\b", texto)
    css = re.search(r"@keyframes", texto) and re.search(r"\banimation(-name)?\s*:", texto)
    assert smil or css, "sem animação (SMIL ou @keyframes + animation)"
    assert ("indefinite" in texto) or ("infinite" in texto), "animação não é em loop"
    assert "<script" not in texto.lower()
    sem_xmlns = re.sub(r'xmlns(:\w+)?="[^"]*"', "", texto)
    assert "http" not in sem_xmlns.lower(), "referência externa"
    for href in re.findall(r'(?:xlink:)?href="([^"]*)"', texto):
        assert href.startswith("#"), f"href externo: {href}"
    for url in re.findall(r"url\(\s*['\"]?([^)'\"]*)", texto):
        assert url.startswith("#"), f"url() externo: {url}"


def test_catalogo_de_exemplo_tem_svg_para_todos():
    cfg = json.loads((RAIZ / "exemplos" / "academia.json").read_text(encoding="utf-8"))
    ids = [e["id"] for e in cfg["exercicios"]]
    assert ids == IDS                                             # os 12 obrigatórios, nesta ordem
    arquivos = sorted(p.stem for p in PASTA.glob("*.svg"))
    assert set(ids) <= set(arquivos) and len(arquivos) >= 12


def test_rotas_svg_e_mp4(dados, tmp_path):
    pasta_mp4 = tmp_path / "mp4"
    pasta_mp4.mkdir()
    (pasta_mp4 / "prancha.mp4").write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64)
    s = Servidor(dados, env={"EXERCICIOS_MP4_DIR": str(pasta_mp4)})
    try:
        api = s.subir()
        st, ctype, corpo = api.raw("/exercicios/prancha.svg")
        assert st == 200 and ctype.startswith("image/svg+xml")
        assert corpo == (PASTA / "prancha.svg").read_bytes()
        assert api.raw("/exercicios/xyz.svg")[0] == 404
        st, ctype, corpo = api.raw("/exercicios/prancha.mp4")
        assert st == 200 and ctype.startswith("video/mp4") and corpo == (pasta_mp4 / "prancha.mp4").read_bytes()
        assert api.raw("/exercicios/agachamento.mp4")[0] == 404
        assert api.raw("/exercicios/../atende")[0] in (400, 404)
    finally:
        s.parar()
