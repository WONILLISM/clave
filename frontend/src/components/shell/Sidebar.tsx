import { Link } from "@tanstack/react-router";
import type { LucideIcon } from "lucide-react";
import {
  LayoutDashboard,
  Terminal,
  FolderOpen,
  Package,
  BookOpen,
  CheckCircle2,
  Trash2,
} from "lucide-react";
import { useHealth } from "~/api/queries";

type NavTo = "/" | "/sessions" | "/projects" | "/artifacts";

type NavItem =
  | { to: NavTo; label: string; icon: LucideIcon; disabled?: false }
  | { to: string; label: string; icon: LucideIcon; disabled: true };

const navItems: NavItem[] = [
  { to: "/", label: "홈", icon: LayoutDashboard },
  { to: "/sessions", label: "세션", icon: Terminal },
  { to: "/projects", label: "프로젝트", icon: FolderOpen },
  { to: "/artifacts", label: "산출물", icon: Package },
  { to: "#", label: "지식", icon: BookOpen, disabled: true },
  { to: "#", label: "작업", icon: CheckCircle2, disabled: true },
];

export function Sidebar() {
  const { data: health } = useHealth();

  return (
    <aside className="flex h-screen w-[180px] shrink-0 flex-col border-r border-outline-variant bg-surface py-4 text-base leading-[1.4] tracking-tight">
      {/* Logo */}
      <div className="mb-8 px-4">
        <div className="font-mono text-md font-bold tracking-tighter text-on-surface">
          CLAVE
        </div>
        <div className="mt-0.5 text-2xs uppercase tracking-widest text-on-surface/30">
          WORKSPACE
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-0.5">
        {navItems.map((item) =>
          item.disabled ? (
            <span
              key={item.label}
              className="flex cursor-not-allowed items-center gap-3 px-4 py-2 text-on-surface/25"
            >
              <item.icon size={18} />
              <span>{item.label}</span>
            </span>
          ) : (
            <Link
              key={item.to}
              to={item.to as NavTo}
              activeOptions={{ exact: item.to === "/" }}
              className="flex items-center gap-3 px-4 py-2 text-on-surface/50 transition-colors duration-150 hover:bg-surface-container-low hover:text-on-surface"
              activeProps={{
                className:
                  "flex items-center gap-3 px-4 py-2 text-on-surface bg-surface-container border-r-2 border-primary",
              }}
            >
              <item.icon size={18} />
              <span>{item.label}</span>
            </Link>
          ),
        )}

        {/* Trash — 분리선 뒤 */}
        <div className="mt-4 border-t border-outline-variant pt-4">
          <span className="flex cursor-not-allowed items-center gap-3 px-4 py-2 text-on-surface/25">
            <Trash2 size={18} />
            <span>휴지통</span>
          </span>
        </div>
      </nav>

      {/* System Live */}
      <div className="mt-auto px-4 py-4">
        <div className="rounded-xs border border-outline-variant bg-surface-container-low p-3">
          <div className="mb-2 flex items-center gap-2">
            <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            <span className="text-2xs uppercase tracking-tighter text-on-surface-variant">
              {health ? "System Live" : "Offline"}
            </span>
          </div>
          <div className="font-mono text-xs text-primary/70">
            {health
              ? `${health.indexed_sessions} sessions`
              : "connecting…"}
          </div>
        </div>
      </div>
    </aside>
  );
}
