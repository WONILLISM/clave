#!/usr/bin/env bash
# Clave - 일괄 검사: 백엔드(ruff + pytest) + 프론트엔드(tsc + vite build).
# 통과 시 침묵, 실패만 출력. CI / pre-commit / 수동에 모두 사용.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UV="${UV:-$HOME/.local/bin/uv}"
[[ -x "$UV" ]] || UV="uv"
BUN="${BUN:-$HOME/.bun/bin/bun}"
[[ -x "$BUN" ]] || BUN="bun"

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

# ── Backend ─────────────────────────────────────────
cd "$REPO_ROOT/backend" || exit 1

run "ruff format --check" "$UV" run --quiet ruff format --check src tests
run "ruff check"          "$UV" run --quiet ruff check src tests
run "pytest"              "$UV" run --quiet pytest -q --tb=short

# ── Frontend ────────────────────────────────────────
cd "$REPO_ROOT/frontend" || exit 1

run "tsc --noEmit"        "$BUN" run lint
run "vite build"          "$BUN" run build

if [[ $FAIL -eq 0 ]]; then
    echo "✓ all checks passed"
fi
exit $FAIL
