#!/usr/bin/env bash
# Congela o contrato: grava o hash de tests/, pytest.ini, spec e dos dois verificadores + o commit-base.
# Rodar UMA vez, depois de responder docs/DECISOES-ABERTAS.md e antes de iniciar o loop/goal.
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
D=longrun/2026-10-05-academia-v1
git diff --quiet && git diff --cached --quiet || { echo "commit o que está pendente antes de congelar" >&2; exit 1; }
h=$(cat $(git ls-files tests pytest.ini docs/ESPECIFICACAO.md $D/verificar-limites.sh $D/verificar-independente.py | sort) | sha256sum | cut -c1-16)
n=$(python3 -m pytest --collect-only -q 2>/dev/null | grep -oE '^[0-9]+ tests? collected' | grep -oE '^[0-9]+')
printf 'HASH=%s\nBASE=%s\nTESTES=%s\n' "$h" "$(git rev-parse HEAD)" "$n" > $D/hash-congelado.txt
git add $D/hash-congelado.txt && git commit -qm "longrun academia-v1: contrato congelado ($h, $n testes)"
echo "congelado: HASH=$h TESTES=$n"
