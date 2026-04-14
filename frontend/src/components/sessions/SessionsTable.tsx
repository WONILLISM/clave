import { useNavigate } from "@tanstack/react-router";
import { Pin } from "lucide-react";
import type { SessionListItem } from "~/api/queries";
import { timeAgo, baseName } from "~/lib/format";

interface Props {
  sessions: SessionListItem[];
}

/** last_message_at 기준 상태 dot 색 */
function dotClass(lastMsg: string): string {
  const age = Date.now() - new Date(lastMsg).getTime();
  const hour = 60 * 60 * 1000;
  const day = 24 * hour;
  if (age < hour) return "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]";
  if (age < day) return "bg-amber-500/80";
  return "bg-emerald-500/40";
}

export function SessionsTable({ sessions }: Props) {
  const navigate = useNavigate();

  return (
    <table className="w-full border-collapse text-left">
      <thead className="sticky top-0 z-[5] bg-surface-dim">
        <tr className="h-8 border-b border-outline-variant">
          <th className="w-10 pl-4 pr-2 font-mono text-2xs uppercase tracking-wider text-on-surface-variant">
            상태
          </th>
          <th className="px-2 font-mono text-2xs uppercase tracking-wider text-on-surface-variant">
            제목
          </th>
          <th className="px-2 font-mono text-2xs uppercase tracking-wider text-on-surface-variant">
            프로젝트
          </th>
          <th className="px-2 font-mono text-2xs uppercase tracking-wider text-on-surface-variant">
            마지막 메시지
          </th>
          <th className="px-2 text-right font-mono text-2xs uppercase tracking-wider text-on-surface-variant">
            메시지
          </th>
        </tr>
      </thead>
      <tbody className="divide-y divide-outline-variant/10">
        {sessions.map((s) => (
          <tr
            key={s.session_id}
            onClick={() =>
              navigate({
                to: "/sessions/$sessionId",
                params: { sessionId: s.session_id },
              })
            }
            className="group h-7 cursor-pointer transition-colors hover:bg-surface-container-low"
          >
            <td className="pl-4 pr-2">
              <div className="flex items-center gap-1">
                <div
                  className={`h-1.5 w-1.5 rounded-full ${dotClass(s.last_message_at)}`}
                />
                {s.pinned && <Pin size={10} className="text-primary" />}
              </div>
            </td>
            <td className="max-w-xs truncate px-2 font-medium text-on-surface transition-colors group-hover:text-primary">
              {s.summary || s.session_id.slice(0, 16) + "…"}
            </td>
            <td
              className="max-w-[160px] truncate px-2 font-mono text-xs text-on-surface-variant"
              title={s.decoded_cwd}
            >
              {baseName(s.decoded_cwd)}
            </td>
            <td className="px-2 text-on-surface-variant/70">
              {timeAgo(s.last_message_at)}
            </td>
            <td className="px-2 text-right font-mono text-xs text-on-surface-variant">
              {s.message_count}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
