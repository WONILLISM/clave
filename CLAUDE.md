# Clave — 에이전트 작업 가이드 (CLAUDE.md)

> 이 파일은 Clave 에서 작업하는 모든 Claude 세션이 자동으로 읽는 **하네스 핵심**.
> 에이전트가 실수할 때마다 그 실수가 다시 일어나지 못하도록 여기에 규칙을 추가한다.

## 프로젝트 한 줄

**Clave** = `~/.claude/` 를 단일 진실 소스로 보고, 세션·산출물·지식·하우스키핑을 한 워크스페이스로 묶는 개인 도구. 자세한 기획은 [`PLAN.md`](./PLAN.md).

## 디렉터리 구조 (W1.5 시점)

```
clave/
├── PLAN.md                # 전체 기획 (수정 시 §14 결정 내역 동기화)
├── CLAUDE.md              # ← 이 파일
├── start.sh               # 백엔드만 / dev 모드 (백엔드+프론트)
├── scripts/check.sh       # ruff + pytest 일괄 검사
├── .claude/
│   ├── settings.json      # 프로젝트-로컬 hooks
│   └── launch.json        # Claude_Preview MCP 용 dev 서버 등록
├── .mcp.json              # Stitch MCP 등 프로젝트 스코프 MCP
├── backend/
│   ├── pyproject.toml     # uv 관리
│   ├── migrations/        # 수제 SQL 마이그레이션 (NNNN_*.sql)
│   ├── src/clave/
│   │   ├── app.py         # FastAPI lifespan
│   │   ├── config.py      # pydantic-settings + ~/.clave/config.toml
│   │   ├── paths.py       # ~/.claude/projects/<encoded> 디코더
│   │   ├── models.py      # pydantic DTO
│   │   ├── overlay/       # SQLite (raw SQL, ORM 금지)
│   │   ├── scanner/       # jsonl 파서·집계·부트스트랩
│   │   └── api/           # FastAPI 라우터
│   └── tests/
└── frontend/              # Vite + React 18 + TS + Tailwind v4 + ark-ui (Bun)
    ├── package.json
    ├── bun.lock           # 텍스트 락파일
    ├── vite.config.ts     # /api → 8765 프록시
    ├── design-refs/       # Stitch HTML 참조 (커밋 안 함)
    ├── scripts/gen-api-types.sh  # OpenAPI → src/api/schema.ts
    └── src/
        ├── main.tsx       # QueryClient + RouterProvider
        ├── styles/        # tokens.css (@theme) + global.css
        ├── api/           # fetch 래퍼 + TanStack Query hooks + schema.ts(자동)
        └── routes/        # TanStack Router 파일기반 (routeTree.gen.ts 자동)
```

## 빌드 / 실행 / 검사

```bash
./start.sh                          # 백엔드만 (127.0.0.1:8765, /docs 에 OpenAPI)
./start.sh dev                      # 백엔드 + 프론트 (5173, /api 는 8765 프록시)
cd backend && uv run pytest         # 16개 테스트
./scripts/check.sh                  # ruff format-check + ruff lint + pytest

cd frontend && bun install          # 프론트 deps (텍스트 락파일 bun.lock)
cd frontend && bun run gen:api      # OpenAPI → src/api/schema.ts (백엔드 떠 있어야)
cd frontend && bun run lint         # tsc --noEmit
cd frontend && bun run build        # dist/ 산출
```

`uv` 는 `~/.local/bin/uv`, `bun` 은 `~/.bun/bin/bun` 에 설치됨. PATH 에 없으면 풀패스로 호출.

## 코딩 규칙 (건축적 제약)

1. **`~/.claude/` 는 read-only.** 어떤 코드도 절대 쓰지 않는다. overlay·trash 는 `~/.clave/` 로.
2. **DB 는 raw SQL + aiosqlite.** SQLAlchemy/Tortoise/Peewee 등 ORM 금지. `tests/test_architecture.py` 가 이를 강제.
3. **모듈 의존성 방향**: `api → scanner, overlay, models, config` / `scanner → overlay, models, config, paths` / `overlay → models, config`. 거꾸로 import 금지 (아키텍처 테스트가 검증).
4. **메시지 본문은 DB 에 저장하지 않는다.** Session detail 은 jsonl 을 그때그때 스트리밍 (W1 정책). FTS5 인덱스는 W3 에서 *요약*만.
5. **pydantic v2 `model_config` 스타일.** v1 `class Config` 사용 금지.
6. **마이그레이션은 추가만**. 기존 `0001_init.sql` 수정 금지. 새 변경은 `0002_*.sql` 신설.
7. **타임존 인지 datetime**: 모든 timestamp 는 `datetime.now(UTC).isoformat(timespec="seconds")` 또는 jsonl 원본 ISO 8601 그대로. naive datetime 금지.
8. **API 응답은 pydantic 모델로**. `dict` 직접 리턴 금지 (OpenAPI 스키마 보존).
9. **테스트 픽스처는 진짜 `~/.claude/` 를 만지지 않는다.** 항상 `tmp_path` 위에 가짜 트리 (`tests/conftest.py` 의 `fake_claude_home` 참조).
10. **커밋 메시지·문서·주석은 한국어** (사용자 선호). 코드 식별자·docstring 은 영어.
11. **프론트엔드 스타일은 Tailwind v4 토큰 기반.** 디자인 토큰은 `frontend/src/styles/tokens.css` 의 `@theme` 블록에 CSS 변수로 정의하고 유틸리티로만 소비한다. **`@apply` 로 컴포넌트 클래스 만들지 않는다** (shadcn 스타일 재현 금지). 다크모드는 `html.dark` class 전략, radius 는 최대 6px, shadow 는 floating layer (팝오버·메뉴·토스트) 에만. UI 프리미티브는 ark-ui 헤드리스 + Tailwind 조합 — shadcn/ui 도입 금지.

## 하네스 자동화 (Hooks)

`.claude/settings.json` 가 다음을 강제:

- **PostToolUse(Edit|Write)** on `backend/**/*.py` → `uv run ruff format <file>` 자동 실행
- **Stop hook** → `uv run ruff check backend/src backend/tests` 통과 못 하면 재작업

`pytest` 는 무거우므로 hook 에서 자동 실행 안 함. 변경 후 직접 `./scripts/check.sh`.

## 출력 정책 ("성공은 조용히, 실패만 크게")

- 검사 스크립트는 통과 시 침묵, 실패 시만 출력.
- 서버 로그는 `rich` 핸들러 (clave/logging_setup.py). DEBUG 가 필요하면 `CLAVE_LOG_LEVEL=DEBUG`.

## 계획-실행 분리

- **비자명한 변경은 plan-mode 로 먼저 합의.** PLAN.md 의 §14 와 충돌하면 PLAN.md 부터 갱신.
- 단순 버그픽스·오타·로그 추가 등은 즉시 진행 가능.

## 자주 하는 실수 — 추가 기록

> 에이전트가 실수할 때마다 한 줄 추가하고, 가능하면 위 "코딩 규칙" 으로 승격시킨다.

- **(2026-04-13)** FK 제약 때문에 sessions upsert 전에 projects upsert 가 와야 한다. `scanner/bootstrap.py` 의 phase 1/phase 2 분리가 그 이유. 한 트랜잭션 안에서 순서 지킬 것.
- **(2026-04-13)** PDF·외부 의존성을 메인 프로젝트 deps 에 추가하지 말 것. 일회성 작업이면 `uvx --from <pkg>` 로 격리 실행.
- **(2026-04-13)** PLAN.md 가 가정한 `~/.claude/agents/`, `skills/`, `tasks/`, `scheduled-tasks/` 디렉터리는 현 Claude Code 버전엔 **없다**. 이 가정에 의존하는 코드 작성 금지 (W4·W5 스코프 재검토 필요).

## 참고

- 상세 기획·결정 내역: [`PLAN.md`](./PLAN.md)
- 백엔드 실행 가이드: [`backend/README.md`](./backend/README.md)
- 하네스 엔지니어링 원전 5가지 구성요소: 컨텍스트(이 파일) · 제약(아키텍처 테스트) · 피드백 루프(check.sh + hooks) · 관측(rich 로그) · HITL(plan mode + 사용자 승인)
