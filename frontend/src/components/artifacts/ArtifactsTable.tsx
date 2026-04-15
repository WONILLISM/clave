import type { ArtifactPathItem } from "~/api/queries";
import { shortenPath, timeAgo } from "~/lib/format";

interface Props {
  items: ArtifactPathItem[];
  onSelectPath: (path: string) => void;
}

/** tool_name → 배지 색조. drawer 와 공유. */
export const TOOL_TONE: Record<string, string> = {
  Write: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  Edit: "bg-sky-500/10 text-sky-600 dark:text-sky-400",
  MultiEdit: "bg-violet-500/10 text-violet-600 dark:text-violet-400",
};

export function ArtifactsTable({ items, onSelectPath }: Props) {
  return (
    <table className="w-full border-collapse text-left">
      <thead className="sticky top-0 z-[5] bg-surface-dim">
        <tr className="h-8 border-b border-outline-variant">
          <th className="px-2 pl-4 font-mono text-2xs uppercase tracking-wider text-on-surface-variant">
            경로
          </th>
          <th className="w-28 px-2 font-mono text-2xs uppercase tracking-wider text-on-surface-variant">
            도구
          </th>
          <th className="w-16 px-2 text-right font-mono text-2xs uppercase tracking-wider text-on-surface-variant">
            수정
          </th>
          <th className="w-16 px-2 text-right font-mono text-2xs uppercase tracking-wider text-on-surface-variant">
            세션
          </th>
          <th className="px-2 font-mono text-2xs uppercase tracking-wider text-on-surface-variant">
            마지막 세션
          </th>
          <th className="w-28 px-2 font-mono text-2xs uppercase tracking-wider text-on-surface-variant">
            마지막 수정
          </th>
        </tr>
      </thead>
      <tbody className="divide-y divide-outline-variant/10">
        {items.map((a) => (
          <tr
            key={a.path}
            onClick={() => onSelectPath(a.path)}
            className="group h-7 cursor-pointer transition-colors hover:bg-surface-container-low"
          >
            <td
              className={`max-w-md truncate px-2 pl-4 font-mono text-xs transition-colors group-hover:text-primary ${
                a.exists
                  ? "text-on-surface"
                  : "text-outline line-through opacity-60"
              }`}
              title={a.path}
            >
              {shortenPath(a.path)}
            </td>
            <td className="px-2">
              <div className="flex flex-wrap gap-1">
                {a.tools.map((t) => (
                  <span
                    key={t}
                    className={`rounded-xs px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider ${
                      TOOL_TONE[t] ?? "bg-outline/10 text-outline"
                    }`}
                  >
                    {t}
                  </span>
                ))}
              </div>
            </td>
            <td className="px-2 text-right font-mono text-xs text-on-surface-variant">
              {a.edit_count}
            </td>
            <td className="px-2 text-right font-mono text-xs text-on-surface-variant">
              {a.session_count}
            </td>
            <td
              className={`max-w-xs truncate px-2 text-on-surface-variant ${a.last_session_summary ? "" : "italic opacity-50"}`}
              title={a.last_session_summary ?? a.last_session_id}
            >
              {a.last_session_summary || a.last_session_id.slice(0, 8)}
            </td>
            <td className="px-2 text-on-surface-variant/70">
              {timeAgo(a.last_modified)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
