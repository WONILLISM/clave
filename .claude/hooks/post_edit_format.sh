#!/usr/bin/env bash
# PostToolUse hook for Edit/Write.
# If the touched file is a Python file under backend/, run ruff format on it.
# Stdin: JSON payload with {tool_input: {file_path: "..."}}.
# Output: silent on success; ruff errors are surfaced.

set -uo pipefail

PAYLOAD="$(cat)"
FILE_PATH="$(printf '%s' "$PAYLOAD" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get("tool_input",{}).get("file_path",""))' 2>/dev/null || true)"

case "$FILE_PATH" in
    *.py)
        ;;
    *)
        exit 0
        ;;
esac

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
case "$FILE_PATH" in
    "$REPO_ROOT"/backend/*) ;;
    *) exit 0 ;;
esac

UV="${UV:-$HOME/.local/bin/uv}"
if [[ ! -x "$UV" ]]; then
    UV="uv"
fi

cd "$REPO_ROOT/backend" || exit 0
"$UV" run --quiet ruff format "$FILE_PATH" >/dev/null 2>&1 || true
exit 0
