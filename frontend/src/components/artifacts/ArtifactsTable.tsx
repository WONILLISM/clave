import { useNavigate } from "@tanstack/react-router";
import type { ArtifactListItem } from "~/api/queries";
import { shortenPath, timeAgo, baseName } from "~/lib/format";

interface Props {
  items: ArtifactListItem[];
}

const TOOL_TONE: Record<string, string> = {
  Write: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  Edit: "bg-sky-500/10 text-sky-600 dark:text-sky-400",
  MultiEdit: "bg-violet-500/10 text-violet-600 dark:text-violet-400",
};

export function ArtifactsTable({ items }: Props) {
  const navigate = useNavigate();

  return (
    <table className="w-full border-collapse text-left">
      <thead className="sticky top-0 z-[5] bg-surface-dim">
        <tr className="h-8 border-b border-outline-variant">
          <th className="w-20 pl-4 pr-2 font-mono text-2xs uppercase tracking-wider text-on-surface-variant">
            도구
          </th>
          <th className="px-2 font-mono text-2xs uppercase tracking-wider text-on-surface-variant">
            경로
          </th>
          <th className="px-2 font-mono text-2xs uppercase tracking-wider text-on-surface-variant">
            세션
          </th>
          <th className="w-40 px-2 font-mono text-2xs uppercase tracking-wider text-on-surface-variant">
            프로젝트
          </th>
          <th className="w-28 px-2 font-mono text-2xs uppercase tracking-wider text-on-surface-variant">
            생성 시각
          </th>
        </tr>
      </thead>
      <tbody className="divide-y divide-outline-variant/10">
        {items.map((a) => (
          <tr
            key={a.artifact_id}
            onClick={() =>
              navigate({
                to: "/sessions/$sessionId",
                params: { sessionId: a.session_id },
              })
            }
            className="group h-7 cursor-pointer transition-colors hover:bg-surface-container-low"
          >
            <td className="pl-4 pr-2">
              <span
                className={`rounded-xs px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider ${
                  TOOL_TONE[a.tool_name] ?? "bg-outline/10 text-outline"
                }`}
              >
                {a.tool_name}
              </span>
            </td>
            <td
              className={`max-w-md truncate px-2 font-mono text-xs transition-colors group-hover:text-primary ${
                a.exists
                  ? "text-on-surface"
                  : "text-outline line-through opacity-60"
              }`}
              title={a.path}
            >
              {shortenPath(a.path)}
            </td>
            <td
              className={`max-w-xs truncate px-2 text-on-surface-variant ${a.session_summary ? "" : "italic opacity-50"}`}
              title={a.session_summary ?? undefined}
            >
              {a.session_summary || "제목 없음"}
            </td>
            <td
              className="max-w-[160px] truncate px-2 font-mono text-xs text-on-surface-variant"
              title={a.session_decoded_cwd ?? undefined}
            >
              {a.session_decoded_cwd ? baseName(a.session_decoded_cwd) : "—"}
            </td>
            <td className="px-2 text-on-surface-variant/70">
              {timeAgo(a.created_at)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
