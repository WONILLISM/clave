import { useState, useCallback } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Copy, Folder, Calendar, Pin, Archive, Trash2 } from "lucide-react";
import { useSession, useSessions } from "~/api/queries";
import { SessionHistoryPane } from "~/components/session-detail/SessionHistoryPane";
import { SessionStream } from "~/components/session-detail/SessionStream";


export const Route = createFileRoute("/sessions/$sessionId")({
  component: SessionDetailPage,
});

function SessionDetailPage() {
  const { sessionId } = Route.useParams();
  const navigate = useNavigate();
  const [offset, setOffset] = useState(0);

  const { data, isPending, error } = useSession(sessionId, offset);
  const meta = data?.session;

  // 같은 프로젝트의 최근 세션 (좌측 패널)
  const { data: siblings } = useSessions(
    meta ? { project_id: meta.project_id, limit: 20 } : undefined,
  );

  const handleLoadMore = useCallback(() => {
    if (data?.has_more) setOffset(data.next_offset);
  }, [data]);

  const handleCopyId = useCallback(() => {
    navigator.clipboard.writeText(sessionId);
  }, [sessionId]);

  if (isPending) {
    return (
      <div className="flex flex-1 items-center justify-center text-on-surface-variant">
        불러오는 중…
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-1 items-center justify-center text-error">
        {String(error)}
      </div>
    );
  }

  if (!data || !meta) return null;

  return (
    <div className="flex h-full">
      {/* Left: history */}
      {siblings && siblings.items.length > 0 && (
        <SessionHistoryPane
          sessions={siblings.items}
          activeId={sessionId}
          onSelect={(id) =>
            navigate({
              to: "/sessions/$sessionId",
              params: { sessionId: id },
            })
          }
        />
      )}

      {/* Right: detail */}
      <section className="relative z-10 flex flex-1 flex-col bg-surface-container shadow-2xl">
        {/* Header */}
        <header className="flex items-start justify-between border-b border-outline-variant/30 p-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h2 className="font-mono text-md font-bold text-on-surface">
                {sessionId}
              </h2>
              <button
                onClick={handleCopyId}
                className="text-outline transition-colors hover:text-primary"
              >
                <Copy size={14} />
              </button>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 rounded border border-outline-variant/30 bg-surface-container-highest px-2 py-0.5">
                <Folder size={14} className="text-outline" />
                <span className="font-mono text-sm text-outline-variant">
                  {meta.decoded_cwd}
                </span>
              </div>
              <div className="flex items-center gap-1.5 text-outline">
                <Calendar size={14} />
                <span className="text-sm">{meta.started_at.slice(0, 10)}</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-1.5 rounded border border-outline-variant/20 px-2 py-1">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
            <span className="font-mono text-xs uppercase tracking-tighter text-outline-variant">
              {meta.message_count}개 메시지
            </span>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          <SessionStream
            messages={data.messages}
            hasMore={data.has_more}
            onLoadMore={handleLoadMore}
          />
        </div>

        {/* Footer actions */}
        <footer className="flex items-center justify-between border-t border-outline-variant/30 bg-surface-variant/70 p-4 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="mx-1 h-6 w-px bg-outline-variant/30" />
            <button
              disabled
              className="flex items-center gap-2 rounded px-3 py-2 text-sm font-medium text-outline opacity-50"
            >
              <Pin size={18} />
              고정
            </button>
            <button
              disabled
              className="flex items-center gap-2 rounded px-3 py-2 text-sm font-medium text-outline opacity-50"
            >
              <Archive size={18} />
              아카이브
            </button>
          </div>
          <button
            disabled
            className="flex items-center gap-2 rounded px-3 py-2 text-sm font-medium text-error-dim opacity-50"
          >
            <Trash2 size={18} />
            세션 삭제
          </button>
        </footer>
      </section>
    </div>
  );
}
