#!/usr/bin/env bash
# Stop hook: run ruff check on the backend.
# Silent on success; lint errors are surfaced as a non-zero exit so the agent sees them.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
UV="${UV:-$HOME/.local/bin/uv}"
[[ -x "$UV" ]] || UV="uv"

cd "$REPO_ROOT/backend" || exit 0

OUT="$("$UV" run --quiet ruff check src tests 2>&1)"
RC=$?
if [[ $RC -ne 0 ]]; then
    echo "ruff check 실패 (Stop hook):" >&2
    echo "$OUT" >&2
    exit 2
fi
exit 0
