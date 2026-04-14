#!/usr/bin/env bash
# OpenAPI → TS 타입 생성. 백엔드가 떠 있어야 함.
set -euo pipefail

cd "$(dirname "$0")/.."

OPENAPI_URL="${OPENAPI_URL:-http://127.0.0.1:8765/openapi.json}"
OUT="src/api/schema.ts"

if ! curl -sSf -o /dev/null "$OPENAPI_URL"; then
  echo "✘ 백엔드 안 떠 있음. './start.sh' 먼저 실행." >&2
  exit 1
fi

bun x openapi-typescript "$OPENAPI_URL" -o "$OUT"
echo "✔ $OUT 생성/갱신"
