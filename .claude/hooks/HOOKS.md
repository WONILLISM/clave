# Clave Hooks 가이드

> 훅은 `.claude/settings.json`에 등록되어 에이전트 생명주기에 자동 실행된다.
> 성공은 조용히, 실패만 크게. (하네스 원칙 6)

## 빠른 참조

| 훅 | 트리거 | 대상 | 동작 | 실패 시 |
|---|---|---|---|---|
| `post_edit_format.sh` | PostToolUse (Edit/Write) | `backend/**/*.py` | `ruff format` 자동 실행 | 무시 (exit 0) |
| `stop_lint.sh` | Stop (턴 종료) | `backend/src` + `tests` | `ruff check` 실행 | **턴 차단** — 에이전트가 수정 후 재시도 |

## 동작 흐름

```
에이전트가 .py 파일 수정
  → [PostToolUse] post_edit_format.sh
    → backend/ 하위 .py 파일이면 ruff format 실행
    → 그 외 파일이면 skip (exit 0)

에이전트가 턴 종료 시도
  → [Stop] stop_lint.sh
    → ruff check 실행
    → 통과 → 조용히 종료 (exit 0)
    → 실패 → stderr에 오류 출력 + exit 2 → 에이전트에게 반환
```

## 설정 위치

`.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write|MultiEdit",
      "hooks": [{
        "type": "command",
        "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/post_edit_format.sh"
      }]
    }],
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/stop_lint.sh"
      }]
    }]
  }
}
```

## 훅 추가 시 규칙

- 성공 시 **침묵** (`exit 0`, stdout 없음)
- 실패 시만 **stderr**로 오류 출력
- `set -uo pipefail` 필수
- `$REPO_ROOT` 기준 상대 경로 사용
- `uv`/`bun` 경로는 환경변수 폴백: `UV="${UV:-$HOME/.local/bin/uv}"`
