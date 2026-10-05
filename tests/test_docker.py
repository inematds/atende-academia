"""Seções 7.4 e 22: entrega em Docker para a VPS e ferramenta de render (checagem estática; o build real e o render ficam no verificar-independente)."""
import os
import re

from conftest import RAIZ


def ler(nome):
    p = RAIZ / nome
    assert p.exists(), f"falta {nome}"
    return p.read_text()


def test_dockerfile():
    d = ler("Dockerfile")
    assert re.search(r"^FROM\s+python:3", d, re.M)
    assert "pip install" not in d
    assert re.search(r"serve.*--host.*0\.0\.0\.0.*--porta.*8080.*--dados.*/dados", d.replace("\n", " ").replace('"', "").replace(",", " "))
    assert "HEALTHCHECK" in d and "/api/saude" in d and "curl" not in d
    assert re.search(r"^COPY\s+.*web", d, re.M)        # os SVGs vão na imagem


def test_compose():
    c = ler("docker-compose.yml")
    for trecho in ("atende:", "build: .", "unless-stopped", "env_file", ".env", "/dados", "127.0.0.1:8080:8080"):
        assert trecho in c, trecho


def test_env_exemplo_tem_todas_as_variaveis_sem_segredo_nem_url():
    e = ler(".env.exemplo")
    for var in ("PUBLIC_URL", "EXERCICIOS_MP4_DIR", "EVOLUTION_URL", "EVOLUTION_API_KEY", "EVOLUTION_INSTANCIA", "WEBHOOK_SEGREDO",
                "TELEGRAM_API_URL", "TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID", "TELEGRAM_SEGREDO"):
        assert re.search(rf"^{var}=\s*$", e, re.M), var           # todas presentes e vazias
    assert not re.search(r"\d{8,10}:[A-Za-z0-9_-]{30,}", e)       # formato de token real do Telegram
    assert "http" not in e.lower()                                # nenhuma URL, nem em comentário


def test_readme_explica_deploy_e_mantem_como_rodar():
    r = ler("README.md")
    assert "Como rodar no seu ambiente" in r      # seção do dono: o implementador acrescenta o deploy sem removê-la
    assert "Deploy na VPS" in r
    for trecho in ("/webhook/evolution/", "MESSAGES_UPSERT", "setWebhook", "secret_token", "./atende backup",
                   "PUBLIC_URL", "tools/render-exercicios"):
        assert trecho in r, trecho


def test_ferramenta_de_render_existe():
    p = RAIZ / "tools" / "render-exercicios"
    assert p.exists(), "falta tools/render-exercicios (seção 7.4)"
    assert os.access(p, os.X_OK), "tools/render-exercicios precisa ser executável"
    t = p.read_text()
    assert t.startswith("#!")
    for trecho in ("hyperframes", "ffprobe", "720", "--saida", "--ids"):
        assert trecho in t, trecho
