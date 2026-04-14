import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Pin } from "lucide-react";
import { useSessions, useProjects } from "~/api/queries";
import { SessionsTable } from "~/components/sessions/SessionsTable";

export interface SessionsSearch {
  project_id?: string;
  pinned?: boolean;
}

export const Route = createFileRoute("/sessions/")({
  component: SessionsPage,
  validateSearch: (search: Record<string, unknown>): SessionsSearch => ({
    project_id: (search.project_id as string) || undefined,
    pinned:
      search.pinned === true || search.pinned === "true"
        ? true
        : search.pinned === false || search.pinned === "false"
          ? false
          : undefined,
  }),
});

function SessionsPage() {
  const { project_id, pinned } = Route.useSearch();
  const navigate = useNavigate({ from: "/sessions/" });

  const { data, isPending, error } = useSessions({
    limit: 200,
    project_id: project_id ?? null,
    pinned: pinned ?? null,
  });

  const { data: projects } = useProjects();

  return (
    <div className="flex flex-1 flex-col overflow-auto bg-surface-dim">
      {/* Filter bar */}
      <div className="flex items-center gap-2 border-b border-outline-variant/10 px-4 py-2">
        {/* Project filter */}
        <select
          value={project_id ?? ""}
          onChange={(e) =>
            navigate({
              search: {
                project_id: e.target.value || undefined,
                pinned,
              },
            })
          }
          className="rounded-xs border border-outline-variant/20 bg-surface-container-high px-2 py-1 font-mono text-xs text-on-surface-variant focus:border-primary focus:outline-none"
        >
          <option value="">모든 프로젝트</option>
          {projects?.map((p) => (
            <option key={p.project_id} value={p.project_id}>
              {p.decoded_cwd}
            </option>
          ))}
        </select>

        {/* Pinned toggle */}
        <button
          onClick={() =>
            navigate({
              search: {
                project_id,
                pinned: pinned ? undefined : true,
              },
            })
          }
          className={`flex items-center gap-1.5 rounded-xs border px-2 py-1 font-mono text-xs transition-colors ${
            pinned
              ? "border-primary bg-primary/10 text-primary"
              : "border-outline-variant/20 bg-surface-container-high text-on-surface-variant hover:border-primary/50"
          }`}
        >
          <Pin size={12} />
          고정됨
        </button>

        {/* Active filter indicators */}
        {(project_id || pinned) && (
          <button
            onClick={() => navigate({ search: {} })}
            className="font-mono text-xs text-outline transition-colors hover:text-error"
          >
            필터 초기화
          </button>
        )}
      </div>

      {/* Content */}
      {isPending && (
        <div className="px-6 py-12 text-center text-on-surface-variant">
          불러오는 중…
        </div>
      )}
      {error && (
        <div className="px-6 py-12 text-center text-error">
          {String(error)}
        </div>
      )}
      {data && data.items.length === 0 && (
        <div className="px-6 py-12 text-center text-on-surface-variant">
          세션이 없습니다.
        </div>
      )}
      {data && data.items.length > 0 && (
        <SessionsTable sessions={data.items} />
      )}
    </div>
  );
}
