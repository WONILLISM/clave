# Clave

> /클라베/ — 라틴어 *clavis*(열쇠). Your key to Claude.

## 이게 뭔가요

**Clave**는 Claude Code와 Claude Cowork를 많이 쓰는 사람을 위한 **개인 워크스페이스**입니다.

Claude를 쓰다 보면 세션이 수십, 수백 개로 쌓입니다. "지난주에 그 API 설계 논의 어디서 했더라?", "이 프로젝트에서 마지막으로 작업한 게 뭐였지?" 같은 질문에 답하려면 `~/.claude/` 안의 jsonl 파일을 직접 뒤져야 합니다. Clave는 이 문제를 풉니다.

## 어떤 문제를 풀어주나

| 문제 | Clave의 해법 |
|---|---|
| **세션 파편화** — 같은 주제가 세션 N개에 흩어져 있음 | 프로젝트별 그룹 + 태그 + 핀으로 묶어서 관리 |
| **맥락 유실** — "그때 뭘 했더라?" 를 찾기 힘듦 | 전체 세션 타임라인 + 메시지 스트림 뷰어 |
| **산출물 흩어짐** — 결과물이 여기저기 퍼져서 못 찾음 | 산출물 인덱싱 + 출처 세션 역참조 (예정) |
| **지식 증발** — 좋은 프롬프트·답변이 일회성으로 사라짐 | Highlight → Knowledge 승격 (예정) |
| **`~/.claude/` 비대** — 오래된 세션·미사용 에이전트가 계속 쌓임 | Housekeeping 정리소 (예정) |

## 핵심 원칙

- **`~/.claude/`는 절대 건드리지 않습니다.** 읽기 전용 관측만 합니다.
- 사용자 메타데이터(핀, 태그, 메모)는 `~/.clave/overlay.sqlite`에 별도 저장합니다.
- 메시지 본문은 DB에 복사하지 않습니다. 열람 시 원본 jsonl에서 직접 읽습니다.

## 현재 할 수 있는 것

### 프로젝트 레지스트리 (`/projects`)

`~/.claude/projects/` 아래의 모든 프로젝트를 자동 인식합니다. 부모 디렉터리 기준으로 그룹화되어 한눈에 볼 수 있고, 각 프로젝트의 세션 수와 마지막 활동 시각을 확인할 수 있습니다.

### 세션 타임라인 (`/sessions`)

모든 Claude Code 세션을 하나의 테이블에서 봅니다. 프로젝트별 필터, 고정(Pin) 필터를 지원합니다. 각 세션의 상태(활성/비활성), 요약, 메시지 수를 한눈에 파악합니다.

### 세션 상세 뷰어 (`/sessions/:id`)

세션을 선택하면 전체 대화 흐름을 볼 수 있습니다.

- **마크다운 렌더링** — 어시스턴트 응답의 코드 블록, 표, 헤딩 등이 보기 좋게 표시됩니다
- **Tool use 카드** — Claude가 사용한 도구(파일 읽기, 편집, 검색 등)를 접어서 보거나 펼쳐서 입력/결과를 확인합니다
- **같은 프로젝트 세션 히스토리** — 좌측에서 같은 프로젝트의 다른 세션으로 빠르게 이동합니다

### Pin / Tag / Rescan

- **Pin** — 중요한 세션을 고정해서 빠르게 찾습니다
- **Tag** — 자유 태그를 붙여서 세션을 분류합니다
- **Rescan** — `~/.claude/`의 변경사항을 수동으로 다시 스캔합니다

## 사용법

### 사전 요구

- **uv** (Python 패키지 매니저): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Bun** (프론트엔드 런타임): `curl -fsSL https://bun.sh/install | bash`

### 설치 및 실행

```bash
git clone <repository-url> clave
cd clave

# 프론트엔드 의존성 설치
cd frontend && bun install && cd ..

# 실행 (백엔드 + 프론트엔드)
./start.sh dev
```

브라우저에서 `http://localhost:5173` 을 열면 됩니다.

최초 실행 시 `~/.claude/`의 세션을 자동 스캔하여 `~/.clave/overlay.sqlite`에 인덱싱합니다. 이후에는 서버 시작 시마다 자동으로 새 세션을 감지합니다.

### 실행 모드

```bash
./start.sh          # 백엔드만 (127.0.0.1:8765, /docs 에 OpenAPI)
./start.sh dev      # 백엔드 + 프론트엔드 (5173 → 8765 프록시)
```

## 아키텍처

```
~/.claude/ (read-only 관측)     Clave (운영·축적·정돈)
┌──────────────────────┐       ┌──────────────────────────┐
│  sessions/*.jsonl    │──────>│  Scanner: 파싱 · 집계     │
│  projects/           │       │  Overlay: Pin·Tag·Note    │
│  settings.json       │       │  SQLite (메타만, 본문 X)   │
│  CLAUDE.md           │       │  API: FastAPI on :8765    │
└──────────────────────┘       │  UI: React + Tailwind v4  │
                               └──────────────────────────┘
```

- **Sources** — `~/.claude/*`는 읽기만. 절대 쓰지 않음.
- **Overlay** — Pin, Tag, Note 등 사용자 메타데이터는 `~/.clave/overlay.sqlite`에 별도 저장.
- **Scanner** — jsonl 세션 파일을 파싱·집계해 SQLite에 인덱싱. 메시지 본문은 DB에 넣지 않고 요청 시 jsonl에서 직접 읽음.

## 스택

| 레이어 | 기술 |
|---|---|
| Backend | Python 3.12 · FastAPI · aiosqlite (raw SQL) · pydantic v2 |
| Frontend | React 18 · TypeScript · Tailwind CSS v4 · TanStack Router/Query · ark-ui |
| 패키지 매니저 | uv (backend) · Bun (frontend) |
| 디자인 | Ink-Leaning 다크 테마 (Stitch 디자인시스템 기반) |

## 개발

```bash
./scripts/check.sh                  # ruff + pytest 일괄 검사
cd backend && uv run pytest         # 백엔드 테스트
cd frontend && bun run lint         # 프론트엔드 타입 체크
cd frontend && bun run gen:api      # OpenAPI -> TS 타입 생성 (백엔드 실행 중이어야)
```

## 로드맵

- [x] Scanner + Overlay DB + 기본 API
- [x] 프로젝트 · 세션 · 세션 상세 화면
- [x] Pin · Tag · Filter · Rescan
- [x] 마크다운 렌더링 · Tool use 확장/축소
- [ ] 전문 검색 (FTS5)
- [ ] Artifact 스캐너 + 세션 연결
- [ ] Highlight -> Knowledge 승격
- [ ] Housekeeping 탐지 룰 + 격리/복원
- [ ] 디바이스 간 동기화

## 라이선스

MIT
