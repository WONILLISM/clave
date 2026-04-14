# Clave — 에이전트 작업 가이드 (CLAUDE.md)

> 이 파일은 Clave에서 작업하는 모든 Claude 세션이 자동으로 읽는 **하네스 핵심**.
> 에이전트가 실수할 때마다 그 실수가 다시 일어나지 못하도록 해결책을 여기에 추가한다.
> — Mitchell Hashimoto, 2026
>
> **하네스 = 컨텍스트 + 제약 + 피드백 루프 + 관측 + HITL**
> — 모델이 올바른 일을 하도록 기대하는 게 아니라, 잘못된 일이 구조적으로 불가능하도록 설계한다.

### 하네스 7원칙

| # | 원칙 | 이 프로젝트에서의 적용 |
|---|---|---|
| 1 | **환경을 설계하라, 코드를 작성하지 마라** | CLAUDE.md + hooks + 아키텍처 테스트가 에이전트 환경 |
| 2 | **실수에서 배우고 영구적으로 방지하라** | 실수 → "자주 하는 실수" 기록 → 코딩 규칙으로 승격 |
| 3 | **제약이 곧 생산성이다** | ORM 금지, 의존성 방향 등 좁은 해결 공간 = 빠른 수렴 |
| 4 | **생성과 평가를 분리하라** | 코드 작성(에이전트) ≠ 검증(ruff, pytest, tsc) |
| 5 | **탈부착 가능하게 유지하라 (Rippable)** | 모델 업그레이드로 불필요해진 규칙은 제거 (§6 참조) |
| 6 | **성공은 조용히, 실패만 크게** | check.sh·hooks 모두 성공 시 침묵, 실패 시만 출력 |
| 7 | **계획과 실행을 분리하라** | 비자명한 변경은 plan mode 먼저 (§5 HITL) |

---

## 1. 컨텍스트 (Context)

> 에이전트가 올바른 시간에 올바른 정보를 갖도록 보장한다.
> 리포지토리가 단일 진실 소스(Single Source of Truth)다.

### 프로젝트 한 줄

**Clave** = `~/.claude/`를 단일 진실 소스로 보고, 세션·산출물·지식·하우스키핑을 한 워크스페이스로 묶는 개인 도구.

### 핵심 문서 맵 (점진적 정보 공개)

> 모든 정보를 이 파일에 넣으면 컨텍스트가 폭발한다.
> CLAUDE.md는 **진입점**이고, 깊은 정보는 링크로 연결한다.

| 문서 | 역할 | 언제 읽나 |
|---|---|---|
| `CLAUDE.md` (이 파일) | 하네스 핵심 — 규칙·제약·루프·관측·HITL | 세션 시작 시 자동 로드 |
| `.claude/agents/AGENTS.md` | 에이전트 역할 빠른 참조 + 작업 흐름 | 에이전트 호출 시 |
| `.claude/hooks/HOOKS.md` | 훅 설명 빠른 참조 + 추가 규칙 | 훅 수정·추가 시 |
| `PLAN.md` | 전체 기획·로드맵·결정 내역 (§14) | 새 기능 설계 시 |
| `backend/README.md` | 백엔드 실행·구조 가이드 | 백엔드 작업 시 |
| `tests/test_architecture.py` | 건축적 제약의 코드 구현 | 제약 위반 에러 발생 시 |

### 디렉터리 구조

```
clave/
├── CLAUDE.md              # ← 이 파일 (하네스 핵심)
├── PLAN.md                # 전체 기획 (수정 시 §14 결정 내역 동기화)
├── start.sh               # 백엔드만 / dev 모드 (백엔드+프론트)
├── scripts/check.sh       # ruff + pytest 일괄 검사
├── .claude/
│   ├── settings.json      # 프로젝트-로컬 hooks (피드백 루프)
│   ├── hooks/             # PostToolUse, Stop 훅 스크립트
│   ├── agents/            # 역할별 에이전트 (AGENTS.md + 개별 .md)
│   └── launch.json        # Claude_Preview MCP 용 dev 서버
├── .mcp.json              # 프로젝트 스코프 MCP 설정
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
│       └── test_architecture.py  # 건축적 제약 강제 (§2 참조)
└── frontend/              # Vite + React 18 + TS + Tailwind v4 + ark-ui (Bun)
    ├── package.json
    ├── vite.config.ts     # /api → 8765 프록시
    └── src/
        ├── styles/        # tokens.css (@theme) + global.css
        ├── api/           # fetch 래퍼 + TanStack Query hooks + schema.ts(자동)
        └── routes/        # TanStack Router 파일기반 (routeTree.gen.ts 자동)
```

### 빌드 / 실행 / 검사

```bash
./start.sh                          # 백엔드만 (127.0.0.1:8765, /docs 에 OpenAPI)
./start.sh dev                      # 백엔드 + 프론트 (5173, /api 는 8765 프록시)
cd backend && uv run pytest         # 테스트
./scripts/check.sh                  # ruff format-check + ruff lint + pytest

cd frontend && bun install          # 프론트 deps (텍스트 락파일 bun.lock)
cd frontend && bun run gen:api      # OpenAPI → src/api/schema.ts (백엔드 떠 있어야)
cd frontend && bun run lint         # tsc --noEmit
cd frontend && bun run build        # dist/ 산출
```

`uv`는 `~/.local/bin/uv`, `bun`은 `~/.bun/bin/bun`에 설치됨. PATH에 없으면 풀패스로 호출.

---

## 2. 제약 (Constraints)

> 해결 공간을 좁혀서 에이전트의 수렴 속도를 높인다 (원칙 3).
> LLM이 아닌 **결정론적 도구**(린터, 구조 테스트)로 기계적으로 강제한다.
> 비결정론적 프롬프트로 품질을 기대하지 않는다.

### 건축적 제약 (코드)

`tests/test_architecture.py`가 아래 3가지를 **pytest로 강제**한다:

| 테스트 | 강제하는 것 |
|---|---|
| `test_no_orm_imports` | SQLAlchemy/Tortoise/Peewee/Alembic/Django import 금지 |
| `test_layering` | 모듈 의존성 방향: `api → scanner → overlay`. 역방향 import 금지 |
| `test_no_writes_under_claude_home` | `~/.claude/` 경로에 쓰기 연산 금지 |

### 코딩 규칙 (불변량)

1. **`~/.claude/`는 read-only.** 어떤 코드도 절대 쓰지 않는다. overlay·trash는 `~/.clave/`로.
2. **DB는 raw SQL + aiosqlite.** ORM 금지. 아키텍처 테스트가 강제.
3. **모듈 의존성 방향**: `api → scanner, overlay, models, config` / `scanner → overlay, models, config, paths` / `overlay → models, config`. 역방향 import 금지. 아키텍처 테스트가 검증.
4. **메시지 본문은 DB에 저장하지 않는다.** Session detail은 jsonl을 그때그때 스트리밍. FTS5 인덱스는 요약만.
5. **pydantic v2 `model_config` 스타일.** v1 `class Config` 사용 금지.
6. **마이그레이션은 추가만.** 기존 `.sql` 수정 금지. 새 변경은 다음 번호로 신설.
7. **타임존 인지 datetime**: `datetime.now(UTC).isoformat(timespec="seconds")` 또는 jsonl 원본 ISO 8601 그대로. naive datetime 금지.
8. **API 응답은 pydantic 모델로.** `dict` 직접 리턴 금지 (OpenAPI 스키마 보존).
9. **테스트 픽스처는 진짜 `~/.claude/`를 만지지 않는다.** 항상 `tmp_path` 위에 가짜 트리.
10. **커밋 메시지·문서·주석은 한국어.** 코드 식별자·docstring은 영어. 커밋 메시지는 아래 "커밋 컨벤션" 참조.
11. **프론트엔드 스타일은 Tailwind v4 토큰 기반.** `@apply` 컴포넌트 클래스 금지, radius 최대 6px, shadow는 floating layer에만. ark-ui 헤드리스 + Tailwind — shadcn/ui 도입 금지.

### 커밋 컨벤션

Conventional Commits 기반, **제목은 한국어**.

```
<type>: <제목> (72자 이내)
                                    ← 빈 줄
- 변경사항 1                         ← 본문 (선택)
- 변경사항 2
```

| 타입 | 용도 | 예시 |
|---|---|---|
| `feat` | 새 기능 | `feat: 세션 상세 마크다운 렌더링` |
| `fix` | 버그 수정 | `fix: pinned 필터 boolean 비교 누락` |
| `refactor` | 동작 변경 없는 구조 개선 | `refactor: SessionStream 컴포넌트 분리` |
| `style` | UI/UX 개선 (기능 변경 없음) | `style: 프로젝트 컬럼 basename 표시` |
| `docs` | 문서 | `docs: README.md 작성` |
| `test` | 테스트 추가·수정 | `test: scanner 파서 엣지케이스 추가` |
| `chore` | 빌드·설정·의존성 | `chore: .gitignore 정비` |
| `perf` | 성능 개선 | `perf: 세션 목록 가상 스크롤 적용` |

규칙: 명령형 현재 시제 · `—` 뒤 보충 설명 허용 · Co-Authored-By 안 씀 · scope 안 씀

---

## 3. 피드백 루프 (Feedback Loops)

> 에이전트의 출력을 **결정론적 검사**(린터, 타입 체커, 테스트)로 즉시 평가하고,
> 실패 시 구조화된 오류 메시지를 반환하여 자체 수정 기회를 제공한다 (원칙 4).
> AI 모델은 자신의 작업을 너무 관대하게 평가한다 — 생성과 평가를 분리해야 한다.

### 자동 훅 (`.claude/settings.json`)

| 훅 | 트리거 | 동작 | 효과 |
|---|---|---|---|
| `post_edit_format.sh` | `Edit`/`Write` on `backend/**/*.py` | `ruff format <file>` 자동 실행 | 포맷 걱정 없이 코드 작성 |
| `stop_lint.sh` | 턴 종료 시 (Stop) | `ruff check backend/src backend/tests` | **lint 실패 시 턴이 끝나지 않음** → 에이전트가 수정 후 재시도 |

### 수동 검사 (`scripts/check.sh`)

```
ruff format --check → ruff check → pytest
```

- `pytest`는 무거우므로 훅에서 자동 실행하지 않음. 변경 후 직접 실행.

### 프론트엔드 검사

```bash
cd frontend && bun run lint    # tsc --noEmit (타입 체크)
cd frontend && bun run build   # 프로덕션 빌드
```

### 피드백 흐름도

```
에이전트가 코드 작성
  → [PostToolUse] ruff format 자동 적용
  → 에이전트가 턴 종료 시도
  → [Stop hook] ruff check 실행
  → 실패? → 에이전트에게 오류 반환 → 자체 수정 → 재시도
  → 성공? → 턴 종료
  → 수동: ./scripts/check.sh (format + lint + pytest 일괄)
```

### 출력 필터링 (원칙 6)

> 테스트 전체 결과(수천 줄)를 컨텍스트에 넣으면 에이전트가 혼란에 빠진다.

- `check.sh`: 통과 시 `✓ all checks passed` 한 줄만 출력. 실패 시만 상세 출력.
- hooks: 성공 시 `exit 0` 침묵. 실패 시만 stderr.
- pytest: `--tb=short` 사용. 전체 traceback 금지.

---

## 4. 관측 (Observation)

> 에이전트와 시스템의 행동을 구조화된 로그로 추적한다.
> "성공은 조용히, 실패만 크게."

### 서버 로그

- **핸들러**: `rich` (컬러 트레이스백, 타임스탬프)
- **기본 레벨**: `INFO` — 스캔 결과, 마이그레이션 적용, 시작/종료
- **디버그**: `CLAVE_LOG_LEVEL=DEBUG` 환경변수로 전환

### 부트스트랩 스캔 로그 (매 서버 시작)

```
clave starting; overlay=~/.clave/overlay.sqlite
applying migration 0002_search.sql
schema version=2
bootstrap scan: projects=16 scanned=16 skipped=0 in 286.7ms
```

### 실수 추적 사이클 (원칙 2)

> "에이전트의 실패 → 원인 분석 → 구조적 해결책 → CLAUDE.md에 반영"

```
에이전트가 실수
  → "자주 하는 실수" 섹션에 날짜 + 한 줄 기록
  → 패턴이 반복되면 "코딩 규칙"(§2)으로 승격
  → 기계적으로 강제 가능하면 test_architecture.py 또는 hook으로 구현
```

---

## 5. HITL (Human-in-the-Loop)

> 고위험 결정에서 인간이 개입할 수 있는 명시적 중단점을 설계한다 (원칙 7).
> "계획 승인 전에 절대 코드를 쓰게 하지 마라." — Boris Tane, Cloudflare

### Plan Mode (계획-실행 분리)

**트리거 — 다음 중 하나라도 해당하면 반드시 plan mode 먼저:**

- 새 기능 구현 (신규 파일 3개 이상 또는 다중 모듈 변경)
- 아키텍처 결정이 필요한 변경
- DB 스키마 변경 (마이그레이션 추가)
- PLAN.md §14 결정 내역과 충돌 가능한 변경

**즉시 진행 가능:**

- 단순 버그 수정, 오타, 로그 추가
- 한 파일 내 리팩터링
- 문서 수정
- UI 미세 조정 (색상, 간격, 텍스트)

### Worktree 격리 구현

plan mode에서 승인된 작업을 실행할 때:

1. 생성된 worktree 디렉터리로 이동하여 작업한다.
2. `AGENTS.md` → `ARCHITECTURE.md` → 관련 문서 순서로 읽는다.
3. **master 브랜치에서 `src/` 코드를 직접 수정하지 않는다.**

### 검증 실행 (필수 — 건너뛸 수 없음)

커밋 전 `bash scripts/check.sh` 를 실행하여 전체 검증:

- 단위 테스트 (pytest)
- 린트 (ruff check)
- 빌드 (frontend: `bun run build`)
- 파일 크기 제한
- 아키텍처 의존성 검사 (`test_architecture.py`)
- 문서 가드닝

**검증을 통과하지 않으면 커밋하지 않는다.**

### 커밋 → 머지

- 커밋 메시지는 Conventional Commits 형식 (§2 커밋 컨벤션 참조)
- `.githooks/pre-commit`이 `scripts/check.sh`를 자동 실행 — 검증 실패 시 커밋 차단

### 사용자 승인 필수 사항

- **커밋**: 사용자가 명시적으로 요청할 때만
- **푸시**: 사용자가 명시적으로 요청할 때만
- **외부 의존성 추가**: 반드시 사용자 확인 후
- **PLAN.md 수정**: plan mode에서 합의 후

---

## 6. 탈부착 원칙 (Rippable Harness)

> 모델이 업그레이드되면 어제의 복잡한 로직이 오늘은 불필요해진다 (원칙 5).
> 하네스는 항상 가볍게 유지하고, 쉽게 제거할 수 있어야 한다.

- 이 파일의 규칙이 **20개를 넘으면** 정리 시점. 불필요해진 규칙을 제거한다.
- 모델이 자연스럽게 지키는 규칙은 삭제 후보. 실패가 3회 이상 재발하는 규칙만 유지.
- hook·테스트로 기계적 강제가 가능하면, 이 파일의 자연어 규칙은 제거해도 됨.

---

## 7. 컨텍스트 내구성 (Context Durability)

> 긴 세션에서 에이전트는 '컨텍스트 불안'을 겪는다 — 컨텍스트 윈도우가 차면 작업 품질이 하락한다.

- **세션이 길어지면**: 단순 압축(compaction)보다 컨텍스트 리셋이 효과적. 인수인계 문서를 남기고 새 세션을 시작한다.
- **이 파일이 진입점**: 새 세션은 CLAUDE.md를 읽는 것만으로 프로젝트 규칙을 복원할 수 있어야 한다. 암묵적 지식을 이 파일에 기록하라.
- **in-context로 접근할 수 없는 정보는 존재하지 않는 것과 같다**: Slack, 구글 문서, 사람 머릿속에만 있는 정보는 에이전트가 사용할 수 없다. 중요한 결정은 PLAN.md §14에 기록.

---

## 자주 하는 실수 — 추가 기록

> 에이전트가 실수할 때마다 한 줄 추가하고, 가능하면 위 "제약" 으로 승격시킨다.

- **(2026-04-13)** FK 제약 때문에 sessions upsert 전에 projects upsert가 와야 한다. `scanner/bootstrap.py`의 phase 1/phase 2 분리가 그 이유. 한 트랜잭션 안에서 순서 지킬 것.
- **(2026-04-13)** PDF·외부 의존성을 메인 프로젝트 deps에 추가하지 말 것. 일회성 작업이면 `uvx --from <pkg>`로 격리 실행.
- **(2026-04-13)** PLAN.md가 가정한 `~/.claude/agents/`, `skills/`, `tasks/`, `scheduled-tasks/` 디렉터리는 현 Claude Code 버전엔 **없다**. 이 가정에 의존하는 코드 작성 금지.
- **(2026-04-14)** contentless FTS5에서 delete하려면 원래 인덱싱된 값을 정확히 전달해야 한다. upsert 전에 기존 값을 조회하고, upsert 후에 FTS를 갱신할 것.
