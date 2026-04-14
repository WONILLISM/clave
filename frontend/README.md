# clave-frontend

Vite + React 18 + TypeScript + Tailwind v4 + ark-ui.
패키지매니저·런타임은 Bun. 자세한 룰은 루트 `CLAUDE.md` §11 참조.

## 실행

```bash
bun install                # 첫 1회 (이후 lockfile 따라감)
bun run gen:api            # 백엔드 떠 있을 때 OpenAPI 타입 생성
bun dev                    # http://localhost:5173 — /api 는 8765 로 프록시
```

또는 루트에서 `./start.sh dev` 로 백엔드 + 프론트 동시 기동.

## 빌드 / 검사

```bash
bun run lint               # tsc --noEmit
bun run build              # dist/
```

## 구조

- `src/styles/tokens.css` — Tailwind v4 `@theme` 디자인 토큰 (Stitch "Clave Ink-Leaning" 추출)
- `src/api/` — fetch 래퍼 + TanStack Query hooks
- `src/routes/` — TanStack Router 파일기반 (자동 codegen → `routeTree.gen.ts`)
- `design-refs/` — Stitch HTML 참조 (저장소 안 커밋, 로컬 비교용)
