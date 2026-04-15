import { Outlet } from "@tanstack/react-router";
import { Sidebar } from "./Sidebar";
import { TopNav } from "./TopNav";

export function AppShell() {
  return (
    <div className="flex h-screen overflow-hidden bg-surface text-on-surface">
      <Sidebar />
      <main className="flex min-w-0 flex-1 flex-col">
        <TopNav />
        <div className="flex-1 overflow-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
