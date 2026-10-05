#!/usr/bin/env bash
# Camada "limite" do goal.md. Imprime LIMITES OK ou o primeiro problema (código ≠ 0).
# Aceita a solução honesta: EVOLUTION_API_KEY, header apikey, @s.whatsapp.net, http://127.0.0.1 e o xmlns do W3C nos SVGs.
# Barra credencial e host externo (não nome de variável) no código, em tools/ e na entrega — a composição do render é só CSS,
# sem GSAP nem CDN (seção 7.4), então tools/ não tem exceção. Barra SMIL nos SVGs (seção 7.1).
set -uo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
D=longrun/2026-10-05-academia-v1
falha() { echo "LIMITE VIOLADO: $*"; exit 1; }
[ -f $D/hash-congelado.txt ] || falha "contrato não congelado (rode $D/congelar.sh)"
source $D/hash-congelado.txt
h=$(cat $(git ls-files tests pytest.ini docs/ESPECIFICACAO.md $D/verificar-limites.sh $D/verificar-independente.py | sort) | sha256sum | cut -c1-16)
[ "$h" = "$HASH" ] || falha "hash do contrato mudou ($h ≠ $HASH)"
git diff --quiet -- tests pytest.ini docs/ESPECIFICACAO.md $D/verificar-independente.py || falha "contrato alterado no working tree"
n=$(python3 -m pytest --collect-only -q 2>/dev/null | grep -oE '^[0-9]+ tests? collected' | grep -oE '^[0-9]+')
[ "$n" = "$TESTES" ] || falha "nº de testes coletados $n ≠ $TESTES"
fora=$( { git diff --name-only "$BASE"; git ls-files --others --exclude-standard; } | sort -u \
  | grep -vE "^($D/|atende$|src/|web/|tools/|exemplos/|README\.md$|VERSION$|Dockerfile$|docker-compose\.yml$|\.env\.exemplo$|\.dockerignore$|\.gitignore$|CLAUDE\.md$|FALHAS\.md$)" )
[ -z "$fora" ] || falha "arquivos fora do escopo: $(echo $fora)"
pesado=$(git ls-files | grep -E '\.mp4$|(^|/)node_modules/' || true)
[ -z "$pesado" ] || falha "mp4 ou node_modules commitado: $(echo $pesado)"
codigo=$(ls -d atende src web 2>/dev/null)
[ -n "$codigo" ] || falha "não há implementação (atende/src/web)"
ferramentas=$(ls -d tools 2>/dev/null || true)
entrega=$(ls Dockerfile docker-compose.yml .env.exemplo .dockerignore 2>/dev/null || true)
grep -rnE '^\s*(import|from)\s+(requests|httpx|aiohttp|urllib3|flask|fastapi|django|openai|anthropic|groq|playwright|PIL|cairosvg)\b' $codigo $ferramentas && falha "dependência externa ou SDK de API"
grep -rnE '(OPENAI|ANTHROPIC|GROQ|OPENROUTER|HEYGEN|MAGNIFIC)_?API_KEY|sk-[A-Za-z0-9]{20,}|[0-9]{8,10}:[A-Za-z0-9_-]{30,}|graph\.facebook|api\.telegram\.org' $codigo $ferramentas $entrega && falha "chave/credencial ou API externa no código, nas ferramentas ou na entrega"
grep -rnP 'https?://(?!127\.0\.0\.1|localhost|www\.w3\.org)' $codigo $ferramentas $entrega && falha "URL externa no código, nas ferramentas ou na entrega"
grep -rlE '<(animate|set)\b' web/exercicios 2>/dev/null && falha "SMIL em web/exercicios (seção 7.1: animação só por CSS)"
grep -rn '0\.0\.0\.0' $codigo && falha "bind em 0.0.0.0 no código (só o comando do container pode passar --host)"
echo "LIMITES OK (hash $HASH, $TESTES testes, escopo ok, sem API/rede)"
