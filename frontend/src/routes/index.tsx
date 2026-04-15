import { createFileRoute } from "@tanstack/react-router";
import { useHealth, useProjects, useSessions, useTags } from "~/api/queries";
import { StatCards } from "~/components/dashboard/StatCards";
import { RecentSessions } from "~/components/dashboard/RecentSessions";
import { ActiveProjects } from "~/components/dashboard/ActiveProjects";
import { TagCloud } from "~/components/dashboard/TagCloud";

export const Route = createFileRoute("/")({
  component: DashboardPage,
});

function DashboardPage() {
  const { data: health } = useHealth();
  const { data: projects } = useProjects();
  const { data: sessions } = useSessions({ limit: 5 });
  const { data: pinnedData } = useSessions({ pinned: true, limit: 100 });
  const { data: tags } = useTags();

  const totalSessions = health?.indexed_sessions ?? 0;
  const totalProjects = projects?.length ?? 0;
  const pinnedSessions = pinnedData?.items.length ?? 0;
  const totalTags = tags?.length ?? 0;

  const recentSessions = sessions?.items ?? [];
  const activeProjects = [...(projects ?? [])]
    .sort(
      (a, b) =>
        new Date(b.last_active_at).getTime() -
        new Date(a.last_active_at).getTime(),
    )
    .slice(0, 5);

  return (
    <section className="flex flex-1 flex-col overflow-auto">
      <div className="border-b border-surface-container-low px-6 py-6">
        <h1 className="text-2xl font-bold tracking-tight text-on-surface">
          Dashboard
        </h1>
        <p className="mt-1 text-base text-on-surface-variant">
          내 Claude 작업 현황
        </p>
      </div>

      <div className="flex flex-col gap-4 px-6 py-6">
        <StatCards
          totalSessions={totalSessions}
          totalProjects={totalProjects}
          pinnedSessions={pinnedSessions}
          totalTags={totalTags}
        />

        <div className="grid grid-cols-2 gap-4">
          <RecentSessions sessions={recentSessions} />
          <ActiveProjects projects={activeProjects} />
        </div>

        {totalTags > 0 && <TagCloud tags={tags!} />}
      </div>
    </section>
  );
}
