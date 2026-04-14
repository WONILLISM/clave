# Clave

> /클라베/ — 라틴어 *clavis*(열쇠). Your key to Claude.

**Clave**는 `~/.claude/`를 단일 진실 소스로 보고, 세션·산출물·지식을 한 워크스페이스로 묶는 **개인 도구**입니다.

기존의 "보는 대시보드"를 넘어, Claude Code와 Claude Cowork를 병행하며 생기는 **세션 파편화 · 산출물 흩어짐 · 지식 증발 · `~/.claude/` 비대** 문제를 풀기 위해 만들어졌습니다.

## 핵심 아키텍처

```
~/.claude/ (read-only 관측)     Clave (운영·축적·정돈)
┌──────────────────────┐       ┌──────────────────────────┐
│  sessions/*.jsonl    │──────▶│  Scanner: 파싱 · 집계     │
│  projects/           │       │  Overlay: Pin·Tag·Note    │
│  settings.json       │       │  SQLite (메타만, 본문 X)   │
│  CLAUDE.md           │       │  API: FastAPI on :8765    │
└──────────────────────┘       │  UI: React + Tailwind v4  │
                               └──────────────────────────┘
```

- **Sources** — `~/.claude/*`는 절대 쓰지 않음. 읽기 전용 관측만.
- **Overlay** — Pin, Tag, Note 등 사용자 메타데이터는 `~/.clave/overlay.sqlite`에 별도 저장.
- **Scanner** — jsonl 세션 파일을 파싱·집계해 SQLite에 인덱싱. 메시지 본문은 DB에 넣지 않고 요청 시 jsonl에서 스트리밍.

## 스택

| 레이어 | 기술 |
|---|---|
| Backend | Python 3.12 · FastAPI · aiosqlite (raw SQL, ORM 금지) · pydantic v2 |
| Frontend | React 18 · TypeScript · Tailwind CSS v4 · TanStack Router/Query · ark-ui (headless) |
| 패키지 매니저 | uv (backend) · Bun (frontend) |
| 디자인 | Ink-Leaning 다크 테마 (Stitch 디자인시스템 기반) |

## 빠른 시작

```bash
# 사전 요구: uv, bun
# uv: curl -LsSf https://astral.sh/uv/install.sh | sh
# bun: curl -fsSL https://bun.sh/install | bash

# 프론트엔드 의존성 설치
cd frontend && bun install && cd ..

# 백엔드만 실행 (127.0.0.1:8765, /docs 에 OpenAPI)
./start.sh

# 백엔드 + 프론트엔드 동시 실행 (5173 → 8765 프록시)
./start.sh dev
```

최초 실행 시 `~/.claude/` 의 세션을 자동 스캔하여 `~/.clave/overlay.sqlite`에 인덱싱합니다.

## 개발

```bash
# 린트 + 테스트 일괄 검사
./scripts/check.sh

# 백엔드 테스트만
cd backend && uv run pytest

# 프론트엔드 타입 체크
cd frontend && bun run lint

# OpenAPI → TypeScript 타입 생성 (백엔드 실행 중이어야 함)
cd frontend && bun run gen:api
```

## 프로젝트 구조

```
clave/
├── CLAUDE.md              # 에이전트 작업 가이드 (코딩 규칙·hooks)
├── PLAN.md                # 전체 기획·결정 내역
├── start.sh               # 백엔드 / dev 모드 실행
├── scripts/check.sh       # ruff + pytest 일괄 검사
├── backend/
│   ├── pyproject.toml
│   ├── migrations/        # 수제 SQL 마이그레이션
│   ├── src/clave/
│   │   ├── app.py         # FastAPI lifespan
│   │   ├── config.py      # pydantic-settings + ~/.clave/config.toml
│   │   ├── models.py      # pydantic DTO
│   │   ├── overlay/       # SQLite (raw SQL)
│   │   ├── scanner/       # jsonl 파서·집계·부트스트랩
│   │   └── api/           # FastAPI 라우터
│   └── tests/
└── frontend/
    ├── package.json
    ├── vite.config.ts     # /api → 8765 프록시
    └── src/
        ├── styles/        # tokens.css (@theme) + global.css
        ├── api/           # fetch 래퍼 + TanStack Query hooks
        └── routes/        # TanStack Router 파일기반
```

## 설계 원칙

1. **`~/.claude/`는 read-only** — 어떤 코드도 절대 쓰지 않는다
2. **DB는 raw SQL** — ORM 금지, 아키텍처 테스트가 강제
3. **메시지 본문은 DB에 저장하지 않는다** — 요청 시 jsonl 스트리밍
4. **Tailwind v4 토큰 기반** — `@apply` 컴포넌트 클래스 금지, 최대 radius 6px
5. **한국어 우선** — 커밋·문서·주석은 한국어, 코드 식별자는 영어

## 라이선스

MIT
