import { Folder } from "lucide-react";
import type { ProjectListItem } from "~/api/queries";
import { timeAgo, parentDir, baseName, shortenPath } from "~/lib/format";

interface Props {
  projects: ProjectListItem[];
}

/** decoded_cwd 부모 디렉터리로 그룹, 각 그룹 내 last_active_at desc */
function groupByParent(projects: ProjectListItem[]) {
  const map = new Map<string, ProjectListItem[]>();
  for (const p of projects) {
    const key = parentDir(p.decoded_cwd);
    const arr = map.get(key) ?? [];
    arr.push(p);
    map.set(key, arr);
  }
  // 그룹 내 정렬 + 그룹 자체 정렬 (가장 최근 활동 기준)
  for (const arr of map.values()) {
    arr.sort(
      (a, b) =>
        new Date(b.last_active_at).getTime() -
        new Date(a.last_active_at).getTime(),
    );
  }
  return [...map.entries()].sort(
    (a, b) =>
      new Date(b[1][0].last_active_at).getTime() -
      new Date(a[1][0].last_active_at).getTime(),
  );
}

export function ProjectsTable({ projects }: Props) {
  const groups = groupByParent(projects);

  return (
    <div>
      {/* Table header */}
      <div className="grid grid-cols-12 border-b border-outline-variant bg-surface-container-low px-6 py-2 font-mono text-2xs uppercase tracking-wider text-outline">
        <div className="col-span-6">경로</div>
        <div className="col-span-3 px-4 text-right">세션 수</div>
        <div className="col-span-3 px-4 text-right">마지막 활동</div>
      </div>

      {groups.map(([group, items]) => (
        <div key={group} className="border-b border-surface-container-low">
          {/* Group header */}
          <div className="flex items-center gap-2 bg-surface px-6 py-1.5">
            <Folder size={12} className="text-primary" />
            <span className="font-mono text-xs tracking-widest text-primary">
              {group}/*
            </span>
          </div>

          {/* Rows */}
          {items.map((p) => (
            <div
              key={p.project_id}
              className="group grid grid-cols-12 items-center border-t border-surface-container-low px-6 py-3 transition-colors hover:bg-surface-container-low"
            >
              <div className="col-span-6 flex flex-col">
                <span className="font-mono text-base text-on-surface transition-colors group-hover:text-primary">
                  {baseName(p.decoded_cwd)}
                </span>
                <span className="font-mono text-xs text-outline" title={p.decoded_cwd}>
                  {shortenPath(p.decoded_cwd)}
                </span>
              </div>
              <div className="col-span-3 px-4 text-right text-base text-on-surface-variant">
                {p.session_count.toLocaleString()}개
              </div>
              <div className="col-span-3 flex items-center justify-end gap-1.5 px-4">
                <span
                  className={`h-1.5 w-1.5 rounded-full ${p.cwd_exists ? "bg-emerald-500" : "bg-outline-variant"}`}
                />
                <span className="text-base text-on-surface-variant">
                  {timeAgo(p.last_active_at)}
                </span>
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
