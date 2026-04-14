#!/usr/bin/env bash
# Clave - dev launcher.
#   ./start.sh         백엔드만 (FastAPI on 127.0.0.1:8765)
#   ./start.sh dev     백엔드 + 프론트 (Vite on 5173, /api 프록시)
set -euo pipefail
cd "$(dirname "$0")"

# uv / bun 이 비대화형 셸 PATH 에 없을 수 있어 보강.
export PATH="$HOME/.local/bin:$HOME/.bun/bin:$PATH"

mode="${1:-backend}"

case "$mode" in
  backend)
    cd backend
    exec uv run --quiet python -m clave
    ;;
  dev)
    # 백엔드를 백그라운드로, 프론트는 포그라운드. Ctrl-C 시 둘 다 정리.
    (cd backend && uv run --quiet python -m clave) &
    backend_pid=$!
    trap 'kill $backend_pid 2>/dev/null || true' EXIT INT TERM
    # 프론트 뜨기 전에 백엔드 health 가 200 찍을 때까지 대기 (uv 첫 실행 시 venv 빌드 1~2초 race 회피).
    printf 'waiting for backend'
    for _ in $(seq 1 60); do
      if curl -fsS -o /dev/null http://127.0.0.1:8765/api/health; then
        printf ' ok\n'
        break
      fi
      if ! kill -0 "$backend_pid" 2>/dev/null; then
        printf '\nbackend exited before becoming healthy\n' >&2
        exit 1
      fi
      printf '.'
      sleep 0.25
    done
    cd frontend
    exec bun --bun vite
    ;;
  *)
    echo "usage: $0 [backend|dev]" >&2
    exit 1
    ;;
esac
