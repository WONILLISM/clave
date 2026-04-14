import { createRootRoute, Outlet } from "@tanstack/react-router";

export const Route = createRootRoute({
  component: RootLayout,
});

function RootLayout() {
  return (
    <div className="min-h-full bg-background text-on-surface">
      <nav className="fixed top-0 z-50 flex h-14 w-full items-center justify-between border-b border-outline-variant/30 bg-background px-6">
        <div className="flex items-center gap-8">
          <span className="font-mono text-lg font-bold tracking-tighter text-on-surface">
            Clave
          </span>
        </div>
        <span className="font-mono text-2xs text-on-surface-variant">
          local · 127.0.0.1:8765
        </span>
      </nav>
      <main className="pt-14">
        <Outlet />
      </main>
    </div>
  );
}
