import { createRootRoute, Link } from "@tanstack/react-router";
import { AppShell } from "~/components/shell/AppShell";

function NotFound() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4">
      <span className="font-mono text-6xl font-bold text-outline-variant/30">
        404
      </span>
      <p className="text-on-surface-variant">페이지를 찾을 수 없습니다.</p>
      <Link
        to="/sessions"
        className="rounded-xs border border-primary px-4 py-2 font-mono text-sm text-primary transition-colors hover:bg-primary/10"
      >
        세션 목록으로
      </Link>
    </div>
  );
}

export const Route = createRootRoute({
  component: AppShell,
  notFoundComponent: NotFound,
});
