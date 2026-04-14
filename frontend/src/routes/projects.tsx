import { createFileRoute } from "@tanstack/react-router";
import { RefreshCw } from "lucide-react";
import { useProjects } from "~/api/queries";
import { ProjectsTable } from "~/components/projects/ProjectsTable";

export const Route = createFileRoute("/projects")({
  component: ProjectsPage,
});

function ProjectsPage() {
  const { data: projects, isPending, error, refetch } = useProjects();

  const total = projects?.length ?? 0;
  const active = projects?.filter((p) => p.cwd_exists).length ?? 0;

  return (
    <section className="flex flex-1 flex-col overflow-auto">
      {/* Header */}
      <div className="border-b border-surface-container-low px-6 py-6">
        <div className="flex items-end justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-on-surface">
              프로젝트 레지스트리
            </h1>
            <p className="mt-1 text-base text-on-surface-variant">
              {total}개 프로젝트에서 {active}개 활성
            </p>
          </div>
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 rounded-xs border border-outline-variant bg-surface-container px-3 py-1.5 font-mono text-sm text-on-surface transition-all hover:bg-surface-container-high"
          >
            <RefreshCw size={14} />
            다시 검색
          </button>
        </div>
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
      {projects && projects.length === 0 && (
        <div className="px-6 py-12 text-center text-on-surface-variant">
          등록된 프로젝트가 없습니다.
        </div>
      )}
      {projects && projects.length > 0 && (
        <ProjectsTable projects={projects} />
      )}
    </section>
  );
}
