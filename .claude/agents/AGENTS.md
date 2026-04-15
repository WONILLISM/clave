# Clave 에이전트 가이드

> 각 에이전트는 `.claude/agents/<name>.md`에 정의되어 있다.
> 호출: `@architect`, `@developer`, `@reviewer`, `@security-sentry`, `@qa-automator`

## 빠른 참조

| 역할 | 에이전트 | 모델 | 도구 권한 | 언제 쓰나 |
|---|---|---|---|---|
| **Architect** (설계자) | `@architect` | opus | Read-only + Agent | 스키마 설계, API 명세, 아키텍처 결정 |
| **UI Designer** (디자이너) | `@ui-designer` | sonnet | Read-only | 신규 화면·빈상태·에러상태·모달·툴바 시각 명세, 디자인시스템 가드 |
| **Developer** (구현자) | `@developer` | sonnet | 전체 (Read/Write/Edit/Bash) | 기능 구현, 버그 수정, 리팩터링 |
| **Reviewer** (검수자) | `@reviewer` | sonnet | Read-only | 코드 리뷰, 컨벤션 체크, 안티패턴 발견 |
| **Security Sentry** (보안관) | `@security-sentry` | sonnet | Read + Bash | SQL 인젝션, XSS, 인증 로직 점검 |
| **QA Automator** (테스터) | `@qa-automator` | sonnet | Read/Write/Edit/Bash | 테스트 작성, 엣지 케이스 발굴, 커버리지 |

## 작업 흐름 예시

```
1. @architect  — 설계 (plan mode)
2. @ui-designer — 시각 명세 (UI 변경 포함 시만, developer 이전)
3. @developer  — 구현 (worktree에서)
4. @reviewer   — 코드 리뷰
5. @security-sentry — 보안 점검
6. @qa-automator — 테스트 작성 + 검증
7. scripts/check.sh 통과 → 커밋
```

**@ui-designer 호출 트리거** — 다음 중 하나라도 해당되면 developer 호출 전에 먼저:
- 신규 페이지·라우트 추가
- 빈상태 / 에러상태 / 로딩상태 화면 (예: 410 "원본 사라짐", 404, empty list)
- 모달·drawer·toast·popover 추가
- 테이블·카드 레이아웃 변경
- 기존 화면에 배지·아이콘·버튼 종류 추가

**즉시 developer 로 가도 되는 경우**:
- 타이포/간격 미세 조정
- 한 컴포넌트의 prop/텍스트 수정
- 버그 픽스

## 핵심 원칙

- **Architect는 코드를 쓰지 않는다** — 설계와 명세만
- **UI Designer는 코드를 쓰지 않는다** — 시각 명세만 (토큰·간격·행동 상태)
- **Reviewer는 코드를 수정하지 않는다** — 분석과 제안만
- **Developer만 코드를 수정한다** — 단, 검증 통과 필수
- **모든 에이전트는 CLAUDE.md 제약을 준수한다**
