import { Link } from "@tanstack/react-router";
import { ArrowRight, Folder } from "lucide-react";
import type { ProjectListItem } from "~/api/queries";
import { timeAgo, baseName } from "~/lib/format";

interface Props {
  projects: ProjectListItem[];
}

export function ActiveProjects({ projects }: Props) {
  return (
    <div className="rounded-sm border border-outline-variant/20 bg-surface-container-low">
      <div className="flex items-center justify-between px-4 py-3">
        <h2 className="text-sm font-semibold text-on-surface">활성 프로젝트</h2>
        <Link
          to="/projects"
          className="flex items-center gap-1 text-2xs text-primary/70 transition-colors hover:text-primary"
        >
          모두 보기 <ArrowRight size={12} />
        </Link>
      </div>
      <div className="divide-y divide-outline-variant/10">
        {projects.map((p) => (
          <Link
            key={p.project_id}
            to="/sessions"
            search={{ project_id: p.project_id }}
            className="flex items-center gap-3 px-4 py-2.5 transition-colors hover:bg-white/5"
          >
            <Folder
              size={14}
              className={
                p.cwd_exists
                  ? "text-emerald-500/70"
                  : "text-on-surface-variant/30"
              }
            />
            <div className="flex min-w-0 flex-1 items-center justify-between gap-2">
              <div className="flex flex-col gap-0.5">
                <span className="truncate text-sm text-on-surface">
                  {baseName(p.decoded_cwd)}
                </span>
                <span className="text-2xs text-on-surface-variant/50">
                  {p.session_count}개 세션
                </span>
              </div>
              <span className="shrink-0 text-2xs text-on-surface-variant/40">
                {timeAgo(p.last_active_at)}
              </span>
            </div>
          </Link>
        ))}
        {projects.length === 0 && (
          <div className="px-4 py-6 text-center text-sm text-on-surface-variant/40">
            프로젝트 없음
          </div>
        )}
      </div>
    </div>
  );
}
