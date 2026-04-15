# 📐 Clave — 신규 프로젝트 기획안

> **Clave** /클라베/ · 라틴어 *clavis*(열쇠) · "Your key to Claude."
> 흩어진 세션·산출물·지식을 여는 **키**, 작업 리듬을 잡는 **클레프**.

작성: 2026-04-13 · 오너: Wonil (AELIQ BD&디지털팀)
코드네임: `clave` · 브랜드: Clave (팀 배포 시 "AELIQ Clave")
레퍼런스: `claude-workspace-dashboard-template` (현 read-only 대시보드)
하네스 가이드: [`CLAUDE.md`](./CLAUDE.md) — 작업 규칙·hooks·자주 하는 실수 기록

---

## 1. 한 줄 정의

> **Clave**는 Claude Cowork + Claude Code를 병행하는 나를 위한, **세션·산출물·지식·자산을 한 뿌리로 묶고 `~/.claude/` 를 건강하게 유지하는 개인 워크스페이스**.
> 기존 대시보드의 "가시성" DNA를 계승하되, *보는 도구* → *운영·축적·정돈하는 도구* 로 진화.

## 2. 왜 만드나 (Pain Points)

네 가지 핵심 페인을 풀이 모든 설계 결정의 기준.

1. **세션/컨텍스트 파편화** — Cowork에서 하던 대화를 Code에서 이어받기 힘들고 그 반대도 마찬가지. 같은 주제가 세션 N개에 흩어져 있음.
2. **산출물/가지 흩어짐** — 결과물이 workspace 폴더·프로젝트 폴더·/mnt·다운로드에 퍼져 나중에 다시 못 찾음.
3. **지식 축적 안 됨** — 좋은 프롬프트·답변·사용 패턴이 일회성으로 증발. 재사용·검색 불가.
4. **에이전트/스킬 발견성 0** — 설치한 건 많은데 언제 뭘 써야 할지 몰라 결국 기본 것만 사용.
5. **`~/.claude/` 비대·난잡** — 실험성 프로젝트, 오래된 세션, 안 쓰는 에이전트·스킬·플러그인이 계속 쌓이면서 디스크·하네스 가시성·수행 속도를 모두 해침. 수동 정리는 무섭고 귀찮음.

## 3. 목표 & 비목표

**목표**
- 내가 하는 모든 Claude 작업(Cowork, Code)의 **단일 진입점**이 된다.
- 세션·프롬프트·산출물·지식을 **하나의 타임라인**에서 조회·이어받기·재사용 가능.
- 개인용으로 4주 내 쓸만하게. 팀 배포는 개인 dogfooding 후 별도 검토.
- 맥미니(자동화 상주) ↔ 맥북(이동 작업) 간 상태 공유.

**비목표**
- 노션 완전 대체 (노션·Figma와 공존. 이건 *Claude 전용* 허브)
- KP Online 서비스 기능 이식 (별개 서비스)
- 범용 CMS/KMS (나/AELIQ팀 맞춤 작업흐름 전용)
- **현 단계에선 팀 배포·다중 사용자 인증 설계 안 함** (개인 MVP 에 집중. 팀 배포 관련 요구사항은 dogfooding 이후 별도 라운드로 분리)

## 4. 레퍼런스 대시보드에서 계승할 것 / 버릴 것

**계승 (DNA)**
- `~/.claude/` 를 **단일 진실 소스**로 보는 구조 — 파일시스템이 곧 DB
- 다크/한글/카드 UX, 14탭 정보 밀집 패턴
- 제로 의존성 지향 (개인용에서는 충분)
- 하네스 건강 점수 같은 **점검형 카드**

**버릴 것**
- 전역 스캔만 가능 → **스코프·태그·pin 으로 소음 제거**
- Read-only mock → **실제 쓰기(메모·태그·하이라이트) 허용** (단 `~/.claude/` 핵심은 여전히 read-only, 쓰기는 별도 저장소)
- 미니파이 JS 단일 번들 → **소스 관리되는 프론트엔드** (유지보수 가능)

## 5. 핵심 개념 모델

```
Workspace
├── Sources   — ~/.claude/* (read-only 관측 대상)
│   ├── Sessions (.jsonl)
│   ├── Projects (cwd별)
│   ├── Agents / Skills / Plugins / Connectors
│   ├── Tasks / Scheduled-tasks / History
│   └── Settings / CLAUDE.md
│
├── Overlay   — 내가 붙이는 메타데이터 (쓰기 허용 영역)
│   ├── Pins          주요 프로젝트/세션/스킬 고정
│   ├── Tags          KP / 메디컬 / 자동화 / 개인 / 실험
│   ├── Notes         세션에 붙이는 내 주석
│   ├── Highlights    세션에서 뽑은 문장·블록
│   └── Links         세션 ↔ 세션 / 프로젝트 ↔ 세션 연결
│
├── Knowledge — Overlay에서 파생된 재사용 자산
│   ├── Prompts       성공한 프롬프트 템플릿
│   ├── Recipes       "이런 상황엔 이 에이전트/스킬 조합" 레시피
│   └── Snippets      산출물 중 재사용 가치 있는 블록
│
└── Artifacts — 산출물 카탈로그 (파일 탐지 + 인덱스)
    ├── 파일시스템 관측 (workspace/*, /mnt/*, 다운로드/*)
    └── 세션과의 출처 연결 (어느 세션에서 나왔는지)
```

## 6. 주요 기능 (MVP 관점)

### P0 — Week 1~2 (개인 사용 즉시 가치)

- ✅ **Unified Timeline** — Cowork+Code 세션을 한 줄로. 날짜·프로젝트·태그·디바이스 필터.
- ✅ **Session Viewer** — 세션 선택하면 메시지·tool_use·산출물 파일 링크를 한 화면.
- ✅ **Pin / Tag** — 세션에 태그·핀 부여. 저장소: `~/.clave/overlay.sqlite`.
- ✅ **Note** — 세션에 메모 부여 (W4).
- ⚠️ **Artifact Tracker** — 1차 구현 완료(W4) 했으나 이벤트 로그 방식이라 signal < noise. 재설계 예정 (W4.5, §14 #9).

### P1 — Week 3 (지식화)

- ⚠️ **Highlight → Knowledge** — 축소판(Create/List/Delete) 만 W4. Knowledge 승격(Prompt/Recipe/Snippet) 은 W4.5 로 분리 (§14 #8).
- ✅ **Search** — Overlay 전역 검색 (SQLite FTS5).
- **Recipe Suggester** — 현재 세션 cwd·파일 타입 보고 "이 작업엔 이 스킬 조합" 힌트. (미착수)

### P2 — Week 4+ (운영 통제 + 정돈 + 나중 확장)

- **Scheduled Task Console** — 예약 작업 on/off·즉시 실행·마지막 결과.
- **Device Sync** — 맥미니/맥북 상태 교차 조회 (본체는 각 기기, overlay만 sync via iCloud Drive 또는 Syncthing).
- **Housekeeping (🧹 `~/.claude/` 정리소)** — 아래 섹션 6-bis 참고. Clave의 핵심 차별 기능.
- **Team-ready Export** — Knowledge 카드를 팀에 공유 가능한 JSON/MD 번들로 export.
- **Project 템플릿 관리자** — CLAUDE.md / agents / skills 세트를 "프로젝트 킷"으로 스탬프.

## 6-bis. Housekeeping — `~/.claude/` 정리소 (핵심 차별 기능)

> **철학**: 삭제는 절대 즉시 하지 않는다. *탐지 → 제안 → 격리(Quarantine) → 유예기간 → 최종 삭제*. 모든 단계에 되돌리기(Undo)와 Dry-run이 있다.

### 탐지 룰 (Detector)

| 카테고리 | 룰 예시 | 기본 제안 |
|---|---|---|
| **오래된 세션** | 마지막 메시지 > 90일, 핀·태그 없음 | 아카이브(압축) |
| **빈/고아 프로젝트** | `~/.claude/projects/<enc>/` 에 jsonl 0개 또는 실제 cwd 디렉토리 삭제됨 | 격리 후 삭제 |
| **중복 프로젝트 폴더** | 같은 cwd가 서로 다른 인코딩으로 2곳 이상 | 병합 제안 |
| **미사용 에이전트** | 최근 180일 tool 로그·세션에서 호출 0회 | 비활성화(파일 유지) |
| **미사용 스킬** | 최근 180일 invoke 0회 + skill-creator 로 만든 초안만 존재 | 격리 후보 |
| **미사용 플러그인/MCP** | `installed_plugins.json` 에 있으나 mcpServers에 미연결 or 호출 로그 0 | 비활성화 제안 |
| **비대 `history.jsonl`** | > 100MB 또는 > 50만 줄 | 연도별 로테이트 → `history-YYYY.jsonl.gz` |
| **고아 태스크** | `tasks/<id>/` 에 상위 세션 jsonl 없음 | 격리 |
| **유통기한 지난 예약작업** | disabled + 마지막 실행 > 60일 | 삭제 제안 |
| **무거운 첨부·이미지 캐시** | `/mnt/uploads`, 세션 내 임시 artifact > 지정 크기 | 용량 랭킹 + 일괄 정리 |
| **스키마 드리프트** | settings.json 에 현 Claude Code에서 deprecated된 키 | 마이그레이션 제안 (읽기만, 자동수정 X) |

### 안전 파이프라인

```
1. Scan (read-only)
     ↓  후보 리스트 생성, 용량·영향 프리뷰
2. Propose (UI 카드)
     ↓  사용자가 체크 → "격리" 클릭
3. Quarantine
     ~/.claude-trash/<timestamp>/...  로 이동 (원본 경로 메타 보존)
     ↓  기본 유예 30일 (설정 가능)
4. Expire & Purge
     유예 경과 후 최종 삭제. 그 전엔 원클릭 복원 가능.
```

- **Dry-run 모드**: 모든 액션은 "미리보기 diff"를 먼저 보여줌. 무엇이 어디로 이동하고 몇 MB 확보되는지.
- **Protected Paths**: `settings.json`, `CLAUDE.md`, `plugins/installed_plugins.json`, 사용자가 핀한 항목은 절대 후보에 오르지 않음.
- **Allowlist / Denylist**: 사용자 정의 경로 규칙. KP Online 관련 폴더는 영구 제외 같은 설정 가능.
- **Journal**: 모든 이동·삭제는 `~/.claude-trash/journal.jsonl` 에 기록. 누구·언제·무엇·크기.
- **Restore CLI**: `clave restore <id>` 한 줄로 복원. UI 버튼도 제공.

### 자동화 레벨

- **L0 (기본)**: 수동. 사용자가 Housekeeping 탭에서 스캔·체크·격리.
- **L1**: 주 1회 스캔 리포트 알림만. 액션은 수동.
- **L2 (과감)**: 특정 카테고리(예: 180일 + 빈 프로젝트)만 자동 격리. 유예기간으로 안전.
- **L3 (비권장)**: 자동 삭제. 기본 비활성·경고.

> **출시 기본값: L0 (완전 수동).** L1~L3 는 Settings 에서 opt-in. 개인 dogfooding 으로 탐지 룰 정확도가 검증된 뒤에 L1 을 권장값으로 승격할지 재평가.

### UI 구성 (Housekeeping 탭)

- 상단: **건강 점수** — 디스크 사용량 / 고아 비율 / 미사용 자산 비율 3 게이지
- 좌측: 카테고리 11개 필터
- 중앙: 카드 리스트. 각 카드 = 항목 + 용량 + 마지막 활동 + "왜 후보인가" 설명 + [격리][제외][핀]
- 우측: **격리 함(Trash)** — 30일 남은 항목, 복원 버튼, 만료 예정
- 하단: **일괄 액션 바** — 체크박스 선택 항목에 "일괄 격리" / "일괄 제외"

### 왜 Clave에 이게 필요한가

1. 대시보드(P0~P1)가 `~/.claude/` 를 *관측*했다면, Housekeeping은 *치유*함. 같은 진실 소스를 공유하므로 자연스럽게 확장.
2. Overlay DB에 쌓인 핀·태그·사용 로그가 "뭐가 중요한지"를 이미 알고 있음 → 정리 제안의 정확도가 높음.
3. 팀 배포 시: 팀원들의 `~/.claude/` 를 건강하게 유지하는 공용 룰셋을 "AELIQ 정리 프리셋"으로 배포 가능.

## 7. 정보 구조 (IA)

- ✅ **Dashboard** (홈) — 통계 카드 + 최근 세션 + 활성 프로젝트 + 태그 분포
- ✅ **Sessions** (Timeline) — 모든 세션, 필터·검색·핀·태그
- ✅ **Projects** — 프로젝트별 뷰
- ✅ **Session Detail** — 메시지·tool_use 마크다운 렌더링 + Notes + Artifacts + Highlights
- ⚠️ **Artifacts** — 1차 목록 구현 (W4). path-grouped 재설계 예정 (W4.5)
- **Knowledge** — Prompts / Recipes / Snippets (미착수, W4.5 에서 Highlight 승격으로 시드)
- **Tasks** — 예약·진행 작업 통제 (미착수)
- **Housekeeping 🧹** — `~/.claude/` 정리소. 탐지·격리·복원·유예 (미착수, W5)
- **Env** — 기존 대시보드의 에이전트·스킬·훅·플러그인·건강점수 (가끔만 보는 탭으로 이전, W6)
- **Settings** — overlay 위치, 스캔 경로, 동기화, 태그 사전, **Protected/Allow/Deny 경로**, 자동화 레벨(L0~L3) (미착수)

## 8. 기술 선택 (개인 MVP)

> 모든 선택은 **"개인 단일 사용자 + 맥 2대"** 라는 전제에 최적화. 팀 배포 시점엔 일부 항목 (DB, 인증, 패키징) 을 재평가한다.

### 8.1 추천 스택 한눈에

| 레이어 | 추천 | 버전/패키지 | 상태 |
|---|---|---|---|
| 런타임 (백엔드) | **Python 3.11+** | 3.11 또는 3.12 | 유지 |
| 웹 프레임워크 | **FastAPI** | `fastapi[standard]` 0.115+ | 유지 |
| ASGI 서버 | **Uvicorn** | 표준 | 유지 |
| 데이터 검증 | **pydantic v2** | FastAPI 동반 | 확정 |
| DB 드라이버 | **sqlite3 (stdlib) + aiosqlite** | stdlib + 0.20 | 확정 |
| 마이그레이션 | **수제 SQL 마이그레이터** | — | 추천 |
| 전문검색 | **SQLite FTS5** | stdlib | 유지 |
| 파일 감시 | **watchdog** | 4.x | 유지 |
| 실시간 푸시 | **FastAPI WebSocket** | 내장 | 유지 |
| 패키징/의존성 | **uv** | 0.5+ | 유지 |
| 작업 스케줄러 | **APScheduler (AsyncIO)** | 3.10+ | 추천 |
| 런타임 구성 | **pydantic-settings + `~/.clave/config.toml`** | 2.x | 추천 |
| 로깅 | **stdlib logging + rich handler** | 13.x | 추천 |
| 테스트 | **pytest + pytest-asyncio + httpx** | 최신 | 추천 |
| 린트/포맷 | **ruff** | 0.7+ | 추천 |
| 프론트 빌드 | **Vite** | 5.x | 유지 |
| 프론트 언어 | **TypeScript** | 5.x | 유지 |
| 프론트 프레임워크 | **React 18** | 18.x | 유지 |
| 스타일 | **Tailwind CSS** | 4.x | 확정 (v4 `@theme` 토큰 기반) |
| UI 프리미티브 | **ark-ui (headless)** | 최신 | 확정 (W1 출발점, shadcn/ui 도입 안 함) |
| 상태관리 | **TanStack Query + Zustand** | query v5, zustand v5 | 추천 |
| 라우팅 | **TanStack Router** 또는 **React Router** | v1 / v7 | 추천 (TanStack 우선) |
| 아이콘 | **lucide-react** | 최신 | 추천 |
| 테이블/가상화 | **TanStack Table + TanStack Virtual** | v8 / v3 | 추천 |
| 날짜 | **date-fns** | 4.x | 추천 |

### 8.2 저장소 배치

- **소스**: `~/.claude/` (read-only 관측). 절대 쓰지 않음.
- **오버레이 (기본값)**: `~/.clave/overlay.sqlite` (SQLite + FTS5). Settings 에서 `~/Library/Application Support/Clave/` 등으로 변경 가능. *"나중 결정"* 항목 (#14 참조) — 기본값으로 출발하되 사용자 변경 가능.
- **격리함**: `~/.clave/trash/<timestamp>/...` + `~/.clave/trash/journal.jsonl`.
- **설정**: `~/.clave/config.toml` (`$CLAVE_CONFIG` 로 오버라이드 가능).
- **디바이스 동기화**: overlay.sqlite 만 iCloud Drive 폴더에 심볼릭 링크. 단일 쓰기 기기 원칙 + WAL 체크포인트 후 동기화.

### 8.3 상세 근거 (각 선택별 Why / Alt / Risk)

**Python 3.11+** — 3.11 의 `TaskGroup` 으로 세션·아티팩트 스캔을 구조적 동시성으로 표현. pydantic v2 가 3.11 에서 가장 성숙. *대안:* Node/Bun — 생태계는 좋지만 파일 파싱·텍스트 처리는 파이썬이 빠르게 짜기 유리. *리스크:* macOS 내장 파이썬 말고 `uv` 로 pinning 해야 재현성 확보.

**FastAPI** — async/await 네이티브라 watchdog 이벤트와 WebSocket 푸시가 자연스럽게 맞물림. 의존성 주입으로 overlay DB 세션·설정 객체를 라우터에 넘기기 편함. 자동 OpenAPI → 프론트 TS 클라이언트 생성 파이프라인이 공짜. *대안:* Flask (async 약함), Starlette 단독 (검증·직렬화 직접). *리스크:* 0.115+ 에서 lifespan/middleware 관례 변경 — 버전 고정.

**Uvicorn** — FastAPI 권장 조합. 개인 MVP 는 단일 워커로 충분. *대안:* Granian (WebSocket 안정성 검증 덜 됨). *리스크:* watchdog 이벤트 루프와 분리하지 않으면 IO 블로킹 → 스캐너는 별도 태스크.

**pydantic v2** — `SessionRow`, `ArtifactRow`, `OverlayCard` 같은 도메인 모델을 그대로 응답 스키마로 재사용. Rust 코어라 빠름. *리스크:* v1 문법으로 쓰면 deprecation 경고 범람 — 처음부터 v2 `model_config` 스타일.

**sqlite3 + aiosqlite** — 개인용 단일 사용자, 수만~수십만 행 규모라 Postgres 과함. WAL 모드로 읽기·쓰기 동시성. *대안:* SQLAlchemy Core (쿼리 단순하므로 raw SQL 이 더 읽기 쉬움). **ORM 은 금지** — 세션 jsonl 의 비정형성에 ORM 레이어가 방해. *리스크:* iCloud 동기화 시 WAL 손상 가능 → WAL 체크포인트 후의 `.sqlite` 만 동기화.

**수제 SQL 마이그레이터** — `schema_version` 테이블 + `migrations/0001_init.sql` 순차 적용. 100줄이면 충분. *대안:* Alembic — ORM 전제라 무거움. *리스크:* 롤백 스크립트 직접 작성 필요하지만 SQLite 백업이 파일 복사라 실용상 OK.

**SQLite FTS5** — 메시지 본문을 가상테이블에 복제해 `MATCH` 로 밀리초 검색. 토크나이저 `unicode61 remove_diacritics 2` + `trigram` 으로 한글 부분검색. *대안:* Meilisearch/Typesense (별도 프로세스). *리스크:* FTS 인덱스 본문의 1~2배 → 세션 요약만 인덱싱, 원본 jsonl 은 안 건드림.

**watchdog** — macOS FSEvents 래퍼. `~/.claude/sessions/`, `~/.claude/projects/<enc>/` 재귀 관찰. *대안:* 폴링 (전력·지연 나쁨). *리스크:* FSEvents 짧은 시간 다량 이벤트 합쳐짐 → 통지만 받고 **재스캔은 디바운스**.

**FastAPI WebSocket** — Timeline 열린 동안 세션 추가/업데이트 즉시 반영. *대안:* SSE (양방향 필요해질 때 한계). *리스크:* 여러 탭 = N 연결 → 필요 시 `BroadcastChannel` 로 탭 리더 동기화.

**uv** — `uv sync` 로 락파일 결정성, `uv run` 으로 venv 활성화 생략. `./start.sh` = `uv run uvicorn ...` 한 줄. *대안:* Poetry (느림), Rye (uv 와 수렴 중). *리스크:* CI 에 `uv` 설치 필요하지만 공식 액션 존재.

**APScheduler (AsyncIO)** — Housekeeping 주간 스캔, Trash 만료 파기, 비대 history 로테이트 같은 주기 작업. FastAPI lifespan 에서 기동/정리. *대안:* Celery (브로커 필요, 과함). cron + 별도 스크립트 (FastAPI 상태 공유 불편). *리스크:* 장시간 작업은 `asyncio.to_thread` 로 오프로드.

**pydantic-settings + `~/.clave/config.toml`** — env·TOML·CLI 옵션을 동일 스키마로. 사용자 편집은 TOML, 자동화는 env, 테스트는 직접 주입. *대안:* dynaconf (타입 체크 약함). *리스크:* `$CLAVE_CONFIG` 오버라이드 지원 필수.

**stdlib logging + rich handler** — 개인 디버깅에 컬러·트레이스백 예쁘게. 팀 배포 시 `structlog` 로 전환. *대안:* loguru (stdlib 핸들러 호환성 이슈).

**pytest + pytest-asyncio + httpx** — FastAPI 공식 테스트 클라이언트 친화. 스캐너 테스트는 `tmp_path` 에 가짜 `~/.claude/` 트리. *리스크:* DB 격리 위해 테스트마다 임시 sqlite.

**ruff** — formatter + linter 통합. 속도 빨라 pre-commit 부담 없음. *대안:* black+isort+flake8 (파편적, 설정 중복).

**Vite** — HMR 빠름, React + Tailwind v4 플러그인 궁합 무난. *대안:* Next.js — 8.4 "도입 안 함" 참조.

**TypeScript** — API DTO 타입 세이프티. `openapi-typescript` 로 pydantic→OpenAPI→TS 자동 생성. *리스크:* 초기 학습비용 있지만 모델 복잡해질수록 이득.

**React 18** — TanStack 생태계 전제. Suspense + concurrent 이 Timeline 가상화에 유용. *대안:* Solid/Svelte (ark-ui·TanStack 수준 생태계 없음).

**Tailwind CSS 4.x** — 유틸리티 퍼스트. `@theme` 블록에 디자인 토큰(`--color-bg`, `--color-surface`, `--color-border`, `--color-accent`, `--font-mono` 등)을 CSS 변수로 등록하고 유틸리티로만 소비. **규칙:** `@apply` 로 컴포넌트 클래스 만들지 않음, 다크모드는 `html.dark` class 전략, radius 는 최대 6px, shadow 는 floating layer 에만. *대안:* CSS Modules / vanilla-extract (토큰 이식은 되지만 유틸리티 속도 없음).

**ark-ui (headless)** — Dialog / Menu / Combobox / Toast 등 접근성 처리만 가져오고 스타일은 Tailwind 로 직접. shadcn/ui 는 도입하지 않는다 — Clave 는 단일 사용자·고밀도 툴이라 shadcn 기본 미학(rounded-2xl + shadow-md + 넉넉한 패딩)과 방향이 반대. *대안:* react-aria-components (a11y 최상이나 번들 큼), Radix 직접 (Dialog/Menu 만 필요하면 OK). *리스크:* ark-ui 가 상대적으로 신생 → 버그 시 Radix 로 개별 교체 여지 남겨둠.

**TanStack Query + Zustand** — Query = 서버상태(세션 목록, 아티팩트) 캐싱·리페치·낙관적 업데이트. Zustand = UI 로컬상태(필터, 선택된 세션, 사이드패널 토글). Redux 는 보일러플레이트 과함. *리스크:* 경계를 "서버에서 온 것=Query, 내 UI 상태=Zustand" 로 엄격히 지킬 것.

**TanStack Router (우선) or React Router v7** — TanStack 은 파일기반 + 타입세이프 loader 로 훌륭하지만 학습곡선. W1 에 부딪혀 보고 불편하면 React Router v7 로 전환 (탭 기반 SPA 라 마이그레이션 비용 낮음).

**lucide-react** — 16px / stroke 1.5px 기본. 트리쉐이킹·라이선스 무난.

**TanStack Table + TanStack Virtual** — Timeline 수천 행 넘으면 일반 렌더로 끊김 → 가상화 필수. Table 은 정렬·필터·그룹핑을 헤드리스로. *대안:* react-window (가볍지만 Table 기능은 직접).

**date-fns** — `formatDistanceToNow` 자주 사용. ESM 트리쉐이킹 유리. *대안:* dayjs (플러그인 기반 번들 관리 귀찮음). Moment 는 deprecated.

### 8.4 명시적으로 도입하지 않을 것 (개인 MVP 단계)

- **Postgres/MySQL** — SQLite 로 충분. 운영부담만 증가. 팀 배포 때 재평가.
- **Redis** — 캐시·pubsub 필요 없음. in-process WebSocket + watchdog 으로 커버.
- **Celery/RQ** — 잡큐 불요. APScheduler 로 충분. 브로커 설치 부담 제거.
- **Alembic** — ORM 전제. 우리는 raw SQL 이라 거슬림. 수제 마이그레이터로 대체.
- **ORM (SQLAlchemy/Tortoise/Peewee)** — 스키마 단순, 세션 jsonl 비정형성에 ORM 이 방해. raw SQL + pydantic 직관적.
- **Next.js** — SSR/SEO 불필요 (로컬 `localhost` 전용). Node 백엔드 중복 (FastAPI 와 역할 겹침). RSC 는 Python 백엔드와 어울리지 않음. Vite SPA 가 정답. *팀 SaaS 전환 시 재검토.*
- **Electron/Tauri** — 네이티브 메뉴·트레이 불요. 브라우저 탭이 가장 빠름. 업데이트·코드사이닝 부담 회피.
- **Docker** — 개인 맥 2대 고정 환경. uv 로 재현성 충분. 컨테이너는 팀 배포 시점에.
- **인증/멀티유저 (Auth0, Supabase Auth 등)** — 비목표. 127.0.0.1 바인딩으로 네트워크 접근 차단.
- **GraphQL** — 엔드포인트 적음. FastAPI REST + OpenAPI 로 충분.
- **Prisma** — Python 백엔드 무관.
- **Zod** — TS 측 런타임 검증 필요할 때만. 우선은 OpenAPI→TS 타입만으로.
- **Storybook** — 비용 대비 가치 낮음. 팀 배포 때.

### 8.5 열어둘 선택

- **iCloud Drive vs Syncthing** — overlay.sqlite 동기화 수단. W6 디바이스 sync 착수 시 실측 후 결정.

(결정 완료: 라우터 → **TanStack Router**, API 클라이언트 → **openapi-typescript**)

### 8.6 디렉터리 구조 (제안)

```
clave/
├── backend/
│   ├── pyproject.toml          # uv 관리
│   ├── src/clave/
│   │   ├── api/                # FastAPI 라우터
│   │   ├── scanner/            # watchdog + jsonl 파서
│   │   ├── overlay/            # SQLite 접근·마이그레이션
│   │   ├── knowledge/          # 프롬프트/레시피/스니펫 승격
│   │   ├── housekeeping/       # 탐지 룰·격리·복원
│   │   └── config.py           # pydantic-settings
│   └── migrations/
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── routes/             # Timeline / Projects / Knowledge / ...
│   │   ├── components/ui/      # ark-ui 래핑 프리미티브 (Button, Dialog, Menu, ...)
│   │   ├── components/domain/  # SessionCard, ArtifactCard 등
│   │   ├── styles/tokens.css   # @theme 토큰 (색·타이포·간격)
│   │   └── lib/api.ts          # 생성된 TS 클라이언트
├── start.sh                    # uv run + vite dev 동시 기동
├── PLAN.md
└── README.md
```

## 9. 데이터 흐름

```
Scanner (watchdog)
  → Parser (.jsonl → SessionRow, cwd별 그룹)
  → Indexer (overlay.sqlite: sessions, messages_fts, artifacts)
  ← Overlay writer (user: pin/tag/note/highlight)
  → API (FastAPI) → UI (React) → 사용자
                              ↓
                      Knowledge promoter
                              ↓
                       overlay.sqlite (knowledge)
```

## 10. 이름

**Clave** /클라베/ · Claude + clavis(열쇠) · "Your key to Claude." (2026-04-13 확정, §14 #1)

<details>
<summary>논의한 후보 (역사 기록)</summary>

Klog (Claude Log), Den (나만의 공간), AELIQ Hub (팀 배포 브랜딩), Lumen (가시성 DNA) — 모두 탈락.

</details>

## 11. 로드맵

| 주차 | 목표 | 산출물 | 상태 |
|---|---|---|---|
| W1 | Scanner + Overlay DB + Timeline·Viewer 뷰 | 세션 타임라인, 핀/태그 동작 | ✅ 완료 |
| W1.5 | 프론트엔드 스캐폴드 + 공통 셸 | Vite+React+TanStack 기반 | ✅ 완료 |
| W2 | Projects·Sessions·Session Detail 통합 | 세 화면 + 인터랙션 (Pin/Tag/Filter/Rescan) | ✅ 완료 |
| W3 | 마크다운 렌더링 + Tool use + FTS5 검색 + 대시보드 홈 | 세션 뷰어 완성 + 검색 + 홈 | ✅ 완료 |
| W4 | Note + Artifact 스캐너 + Highlight (축소판) | Note CRUD + Artifact 목록 + Highlight 선택·저장 | ✅ 완료 (Knowledge 승격은 다음 라운드) |
| W4.5-A | Artifact 재설계 (path 중심) | `/artifacts` path-grouped + 세션 역참조 drawer + 세션 상세 ArtifactsPanel 제거 | ✅ 완료 |
| W4.5-B | Highlight → Knowledge 승격 (Prompt/Recipe/Snippet) | — | ⏸ 보류 (데이터 축적 후 §14 #10) |
| W5-MVP0 | **Housekeeping 탐지 (read-only)** | 🧹 `/housekeeping` 탭 — 룰 3개 (오래된 세션 / 빈 프로젝트 / 고아 프로젝트), 액션 없음 | ✅ 완료 |
| W5-MVP1 | Housekeeping 격리 파이프라인 | `~/.clave-trash/` 이동 + 30일 유예 + 복원 + Journal | 🔜 다음 (dogfooding 후 착수) |
| W5-MVP2 | Housekeeping 추가 탐지 룰 + 자동화 L1 | 비대 history.jsonl·미사용 플러그인·중복 프로젝트 등, 주 1회 스캔 리포트 | 후속 |
| W6 | Scheduled task console + 디바이스 sync + Env 탭 이식 | 팀 배포 전 안정화 | |
| W7+ | Team export, 템플릿 관리자, 권한 모델, AELIQ 정리 프리셋 | 팀 배포 베타 | |

## 12. 리스크 & 대응

- **~/.claude 스키마 변경 리스크**: Claude Code 업데이트로 jsonl 포맷이 바뀔 수 있음 → 파서는 스키마 버전 감지 + graceful degradation.
- **overlay 충돌(다기기)**: SQLite를 iCloud로 공유하면 동시 쓰기 시 일부 손실 가능 → 단일 쓰기 기기 원칙 + 변경 로그 저널링.
- **스코프 크립**: "노션 대체" 유혹에 빠지면 실패 → 모든 기능은 "Claude 세션과 연결되어야 한다"는 제약.
- **팀 배포 보안**: Overlay에 민감 프롬프트가 쌓일 수 있음 → export 시 민감도 태그 기반 자동 마스킹.
- **Housekeeping 오판**: 실제론 중요한데 "미사용"으로 잡힐 위험 → Protected Paths + 30일 유예 + Journal 로 복원 보장. 기본 L0/L1, L3 은 UI에서 더블 확인.
- **Trash 디스크 점유**: 격리함 자체가 비대해질 수 있음 → Trash 상단에 총 용량 + 자동 만료 카운트다운 표시.

## 13. 레퍼런스 대시보드 재활용 전략 (역사)

> W1 시점 결정. 이제 참조용.

- **즉시 재활용**: 한글 라벨 사전(에이전트 71 + 스킬 102), 다크 팔레트, 파싱 로직(settings/plugins/mcp)
- **리팩터링 후 이식**: 하네스 건강 점수 계산식 → Env 탭으로 축소 이전 (W6)
- **버렸다**: 미니파이 SPA 번들, read-only mock 엔드포인트

## 14. 결정 내역

(2026-04-13 확정)

| # | 항목 | 결정 | 비고 |
|---|---|---|---|
| 1 | 이름 | **Clave** ✅ | 기존 확정 유지 |
| 2 | 도메인/깃허브 선점 | **하지 않음** | 개인용 단계엔 불필요. 팀/SaaS 전환 시 재논의 |
| 3 | P0 첫 착수 기능 | **Timeline 먼저** | Artifact Tracker 는 W2 |
| 4 | overlay·trash 저장 위치 | **보류 — 착수 전 재확인** | 기본값 `~/.clave/` 로 출발, Settings 에서 변경 가능 (§8.2) |
| 5 | 프론트엔드 출발점 | **Tailwind v4 + ark-ui 확정** | shadcn/ui 도입 안 함 — 고밀도·단일 사용자 툴 성격상 shadcn 기본 미학과 방향 불일치. 토큰은 `@theme` 에 정의, Stitch 로 화면 목업 생성 후 이식 (§8.1, §8.3) |
| 6 | Housekeeping 기본 자동화 레벨 | **L0 (완전 수동)** | L1~L3 는 Settings opt-in (§6-bis) |
| 7 | 팀 배포 시점 | **현 단계 고려 안 함** | §3 비목표로 명시. 개인 dogfooding 후 별도 라운드 |
| 8 | W4 Highlight 범위 | **축소판 (Create/List/Delete 만)** | 2026-04-15. Knowledge 승격(Prompt/Recipe/Snippet) 은 분리 — 하이라이트 데이터 쌓인 뒤 패턴 보고 승격 UX 설계. `kind` 컬럼만 미리 두고 값은 `"insight"` 고정 |
| 9 | Artifact 재설계 방향 | **A: path 중심 카탈로그 + 세션 역참조** | 2026-04-15. 현 이벤트 로그 방식은 signal < noise (같은 파일 Write/Edit 반복 → 중복 행, tool_use 카드와 정보 겹침, 파일→세션 역참조 불가). 다음 라운드에서 `/artifacts` 를 `1 path = 1 행` (수정 횟수 + 마지막 세션) 으로 재구성, 파일 행 클릭 시 세션들 drawer, 세션 상세의 ArtifactsPanel 은 제거. **W4.5-A 로 commit 89ab29a 완료** |
| 10 | W4.5-B Highlight → Knowledge 승격 | **보류** | 2026-04-15. 하이라이트 데이터 충분히 쌓이지 않은 상태에서 Prompt/Recipe/Snippet 승격 UX 설계는 허공 작업. dogfooding 으로 50개+ 누적되어 패턴이 보이면 재개 |
| 11 | W5 Housekeeping 단계 분할 | **MVP-0 (탐지) → MVP-1 (격리·복원) → MVP-2 (추가 룰·자동화)** | 2026-04-15. 11개 룰 × 격리 파이프라인 × L0~L3 자동화 한 번에 붙이면 스코프 폭발. 실제 `~/.claude/` 실측 결과 agents/·skills/·tasks/·scheduled-tasks/ 부재 → 룰 11개 중 실효 3개. MVP-0 (탐지 전용 read-only) **완료 commit 64dd0ae** — dogfooding 으로 룰 정확도 검증 후 MVP-1 격리 설계 정확도 ↑ |

### 다음 라운드 (착수 전 확정 필요)

- 디바이스 sync 수단 (iCloud Drive vs Syncthing) — W6 착수 시 실측 후 결정

(확정 완료: overlay·trash 경로 = `~/.clave/` 기본값 유지, 라우터 = TanStack Router)

### 미래 플랜: 팀 하네스 (Cowork + Box Drive)

> (2026-04-14 논의, 추후 별도 라운드로 진행)

**배경**: 개발자는 Claude Code + CLAUDE.md로 하네스를 구축하지만, 비개발 직원(의학라이터, 디자이너, 기획자)은 **Claude Cowork**을 사용한다. 이들에게도 하네스 엔지니어링을 적용하려면 Cowork의 "프로젝트 지식 베이스" 기능을 활용해야 한다.

**구상**:
- **Box Drive 루트**: 글로벌 `CLAUDE.md` (회사 공통 규칙) + 직군별 템플릿
- **프로젝트 생성 시**: 글로벌 + 직군별 템플릿을 조합해 프로젝트 전용 `CLAUDE.md` 자동 생성
- **Cowork 지식 베이스**: 프로젝트 폴더를 지정하면 해당 폴더 내 `CLAUDE.md`가 하네스로 작동
- **제약**: Cowork은 지식 베이스 폴더 상위를 탐색 불가 → 프로젝트 폴더에 필요한 모든 컨텍스트가 있어야 함

**Clave와의 관계**: Clave는 개인용 범용 도구로 public 유지. 회사 콘텐츠(템플릿, 규칙)는 Box Drive에 격리. Clave에 팀 기능을 넣으려면 GitHub private 전환 필요 → 현 단계에서는 분리 유지.
