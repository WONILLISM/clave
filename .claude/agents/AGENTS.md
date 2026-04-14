# Clave 에이전트 가이드

> 각 에이전트는 `.claude/agents/<name>.md`에 정의되어 있다.
> 호출: `@architect`, `@developer`, `@reviewer`, `@security-sentry`, `@qa-automator`

## 빠른 참조

| 역할 | 에이전트 | 모델 | 도구 권한 | 언제 쓰나 |
|---|---|---|---|---|
| **Architect** (설계자) | `@architect` | opus | Read-only + Agent | 스키마 설계, API 명세, 아키텍처 결정 |
| **Developer** (구현자) | `@developer` | sonnet | 전체 (Read/Write/Edit/Bash) | 기능 구현, 버그 수정, 리팩터링 |
| **Reviewer** (검수자) | `@reviewer` | sonnet | Read-only | 코드 리뷰, 컨벤션 체크, 안티패턴 발견 |
| **Security Sentry** (보안관) | `@security-sentry` | sonnet | Read + Bash | SQL 인젝션, XSS, 인증 로직 점검 |
| **QA Automator** (테스터) | `@qa-automator` | sonnet | Read/Write/Edit/Bash | 테스트 작성, 엣지 케이스 발굴, 커버리지 |

## 작업 흐름 예시

```
1. @architect  — 설계 (plan mode)
2. @developer  — 구현 (worktree에서)
3. @reviewer   — 코드 리뷰
4. @security-sentry — 보안 점검
5. @qa-automator — 테스트 작성 + 검증
6. scripts/check.sh 통과 → 커밋
```

## 핵심 원칙

- **Architect는 코드를 쓰지 않는다** — 설계와 명세만
- **Reviewer는 코드를 수정하지 않는다** — 분석과 제안만
- **Developer만 코드를 수정한다** — 단, 검증 통과 필수
- **모든 에이전트는 CLAUDE.md 제약을 준수한다**
