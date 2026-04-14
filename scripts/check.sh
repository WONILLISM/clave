#!/usr/bin/env bash
# Clave - 일괄 검사: ruff format 확인 + ruff lint + pytest.
# 통과 시 침묵, 실패만 출력. CI / pre-commit / 수동에 모두 사용.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UV="${UV:-$HOME/.local/bin/uv}"
[[ -x "$UV" ]] || UV="uv"

cd "$REPO_ROOT/backend" || exit 1

FAIL=0

run() {
    local label="$1"
    shift
    local OUT
    OUT="$("$@" 2>&1)"
    local RC=$?
    if [[ $RC -ne 0 ]]; then
        echo "❌ $label" >&2
        echo "$OUT" >&2
        FAIL=1
    fi
}

run "ruff format --check" "$UV" run --quiet ruff format --check src tests
run "ruff check"          "$UV" run --quiet ruff check src tests
run "pytest"              "$UV" run --quiet pytest -q

if [[ $FAIL -eq 0 ]]; then
    echo "✓ all checks passed"
fi
exit $FAIL
