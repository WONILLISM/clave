import { useNavigate } from "@tanstack/react-router";
import { Link } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";
import type { SessionListItem } from "~/api/queries";
import { timeAgo, baseName } from "~/lib/format";

/** last_message_at 기준 상태 dot 색 */
function dotClass(lastMsg: string): string {
  const age = Date.now() - new Date(lastMsg).getTime();
  const hour = 60 * 60 * 1000;
  const day = 24 * hour;
  if (age < hour) return "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]";
  if (age < day) return "bg-amber-500/80";
  return "bg-emerald-500/40";
}

interface Props {
  sessions: SessionListItem[];
}

export function RecentSessions({ sessions }: Props) {
  const navigate = useNavigate();

  return (
    <div className="rounded-sm border border-outline-variant/20 bg-surface-container-low">
      <div className="flex items-center justify-between px-4 py-3">
        <h2 className="text-sm font-semibold text-on-surface">최근 세션</h2>
        <Link
          to="/sessions"
          className="flex items-center gap-1 text-2xs text-primary/70 transition-colors hover:text-primary"
        >
          모두 보기 <ArrowRight size={12} />
        </Link>
      </div>
      <div className="divide-y divide-outline-variant/10">
        {sessions.map((s) => (
          <button
            key={s.session_id}
            type="button"
            onClick={() =>
              navigate({
                to: "/sessions/$sessionId",
                params: { sessionId: s.session_id },
              })
            }
            className="flex w-full items-center gap-3 px-4 py-2.5 text-left transition-colors hover:bg-white/5"
          >
            <div
              className={`h-1.5 w-1.5 shrink-0 rounded-full ${dotClass(s.last_message_at)}`}
            />
            <div className="flex min-w-0 flex-1 flex-col gap-0.5">
              <span className={`truncate text-sm ${s.summary ? "text-on-surface" : "italic text-on-surface-variant/50"}`}>
                {s.summary || "제목 없음"}
              </span>
              <span className="flex items-center gap-2 text-2xs text-on-surface-variant/50">
                <span>{baseName(s.decoded_cwd)}</span>
                <span>·</span>
                <span>{timeAgo(s.last_message_at)}</span>
                <span>·</span>
                <span>{s.message_count}건</span>
              </span>
            </div>
          </button>
        ))}
        {sessions.length === 0 && (
          <div className="px-4 py-6 text-center text-sm text-on-surface-variant/40">
            세션 없음
          </div>
        )}
      </div>
    </div>
  );
}
