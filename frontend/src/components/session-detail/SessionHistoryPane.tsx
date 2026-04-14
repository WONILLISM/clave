import type { SessionListItem } from "~/api/queries";
import { timeAgo } from "~/lib/format";

interface Props {
  sessions: SessionListItem[];
  activeId: string;
  onSelect: (id: string) => void;
}

export function SessionHistoryPane({ sessions, activeId, onSelect }: Props) {
  return (
    <section className="h-full w-[40%] shrink-0 overflow-y-auto border-r border-outline-variant/20 bg-surface-dim opacity-50 transition-opacity hover:opacity-100">
      <div className="space-y-4 p-4">
        <div className="flex items-end justify-between">
          <span className="font-mono text-xs uppercase tracking-wider text-outline">
            히스토리
          </span>
          <span className="font-mono text-2xs text-outline/40">
            {sessions.length}개 세션
          </span>
        </div>

        <div className="space-y-[2px]">
          {sessions.map((s) => {
            const isActive = s.session_id === activeId;
            return (
              <div
                key={s.session_id}
                onClick={() => onSelect(s.session_id)}
                className={`cursor-pointer border-l-2 p-3 transition-colors ${
                  isActive
                    ? "border-primary bg-surface-container"
                    : "border-transparent hover:bg-surface-container-low"
                }`}
              >
                <div className="mb-1 flex items-start justify-between">
                  <span
                    className={`font-mono text-sm ${isActive ? "text-primary" : "text-outline"}`}
                  >
                    {s.session_id.slice(0, 13)}…
                  </span>
                  <span
                    className={`text-2xs ${isActive ? "text-outline" : "text-outline/50"}`}
                  >
                    {timeAgo(s.last_message_at)}
                  </span>
                </div>
                <p
                  className={`truncate text-base leading-tight ${isActive ? "text-on-surface" : "text-outline/80"}`}
                >
                  {s.summary || "제목 없음"}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
