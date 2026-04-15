#!/usr/bin/env bash
# Clave - dev launcher.
#   ./start.sh         백엔드만 (FastAPI on 127.0.0.1:8765)
#   ./start.sh dev     백엔드 + 프론트 (Vite on 5173, /api 프록시)
#   ./start.sh status  현재 떠 있는 백엔드/프론트 확인 (pid + health)
#   ./start.sh stop    백엔드(8765) + 프론트(5173) 둘 다 종료 (TERM → KILL)
set -euo pipefail
cd "$(dirname "$0")"

# uv / bun 이 비대화형 셸 PATH 에 없을 수 있어 보강.
export PATH="$HOME/.local/bin:$HOME/.bun/bin:$PATH"

mode="${1:-backend}"

# ANSI — tty 일 때만 색. 파이프/리다이렉트엔 plain.
if [ -t 1 ]; then
  C_OK=$'\033[32m'; C_ERR=$'\033[31m'; C_DIM=$'\033[2m'; C_RST=$'\033[0m'
else
  C_OK=""; C_ERR=""; C_DIM=""; C_RST=""
fi

# 포트 상태 한 줄 출력: "backend  8765  up    pid=62986  health=200  reload=on"
report_port() {
  local label="$1" port="$2" health_path="${3:-}"
  local pids pid procinfo
  pids=$(lsof -ti ":${port}" 2>/dev/null || true)
  if [ -z "$pids" ]; then
    printf "  %-8s :%s  %sdown%s\n" "$label" "$port" "$C_ERR" "$C_RST"
    return
  fi
  pid=$(echo "$pids" | head -n 1)
  procinfo=$(ps -o comm= -p "$pid" 2>/dev/null | head -n 1 | awk -F/ '{print $NF}')
  printf "  %-8s :%s  %sup%s    pid=%s (%s)" \
    "$label" "$port" "$C_OK" "$C_RST" "$pid" "${procinfo:-?}"
  if [ -n "$health_path" ]; then
    local code
    code=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 2 \
      "http://127.0.0.1:${port}${health_path}" 2>/dev/null || echo "---")
    if [ "$code" = "200" ]; then
      printf "  health=%s%s%s" "$C_OK" "$code" "$C_RST"
    else
      printf "  health=%s%s%s" "$C_ERR" "$code" "$C_RST"
    fi
  fi
  # reload 감지 — uvicorn --reload 는 부모 + 자식 2프로세스.
  if [ "$label" = "backend" ] && [ "$(echo "$pids" | wc -l | tr -d ' ')" -gt 1 ]; then
    printf "  %sreload=on%s" "$C_DIM" "$C_RST"
  fi
  printf "\n"
}

# 포트 종료: SIGTERM → 최대 3초 대기 → 남아있으면 SIGKILL. 결과 한 줄 출력.
stop_port() {
  local label="$1" port="$2" pids
  pids=$(lsof -ti ":${port}" 2>/dev/null || true)
  if [ -z "$pids" ]; then
    printf "  %-8s :%s  %salready down%s\n" "$label" "$port" "$C_DIM" "$C_RST"
    return
  fi
  # shellcheck disable=SC2086
  kill $pids 2>/dev/null || true
  for _ in $(seq 1 15); do
    sleep 0.2
    lsof -ti ":${port}" >/dev/null 2>&1 || break
  done
  if lsof -ti ":${port}" >/dev/null 2>&1; then
    pids=$(lsof -ti ":${port}" 2>/dev/null || true)
    # shellcheck disable=SC2086
    kill -9 $pids 2>/dev/null || true
    printf "  %-8s :%s  %sstopped (SIGKILL)%s\n" "$label" "$port" "$C_ERR" "$C_RST"
  else
    printf "  %-8s :%s  %sstopped%s\n" "$label" "$port" "$C_OK" "$C_RST"
  fi
}

case "$mode" in
  backend)
    cd backend
    exec uv run --quiet python -m clave
    ;;
  status)
    report_port backend  8765 /api/health
    report_port frontend 5173
    exit 0
    ;;
  stop)
    stop_port backend  8765
    stop_port frontend 5173
    exit 0
    ;;
  dev)
    # 백엔드를 백그라운드로, 프론트는 포그라운드. Ctrl-C 시 둘 다 정리.
    # CLAVE_RELOAD=1 — backend/src/ 변경 시 uvicorn 자동 재기동 (DELETE 같은 신규
    # 라우트 추가 후 재기동 깜빡임 방지).
    (cd backend && CLAVE_RELOAD=1 uv run --quiet python -m clave) &
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
    echo "usage: $0 [backend|dev|status|stop]" >&2
    exit 1
    ;;
esac
