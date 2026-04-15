import { useState, useCallback, useRef } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import {
  Copy,
  Folder,
  Calendar,
  Pin,
  PinOff,
  Tag,
  X,
} from "lucide-react";
import {
  useSession,
  useSessions,
  useTags,
  useNotes,
  useHighlights,
} from "~/api/queries";
import {
  usePinSession,
  useUnpinSession,
  useAttachTag,
  useDetachTag,
  useCreateNote,
  useUpdateNote,
  useDeleteNote,
  useCreateHighlight,
  useDeleteHighlight,
} from "~/api/mutations";
import { shortenPath } from "~/lib/format";
import { SessionHistoryPane } from "~/components/session-detail/SessionHistoryPane";
import { SessionStream } from "~/components/session-detail/SessionStream";
import { NotesPanel } from "~/components/session-detail/NotesPanel";
import { HighlightsPanel } from "~/components/session-detail/HighlightsPanel";
import { HighlightSelectionToolbar } from "~/components/session-detail/HighlightSelectionToolbar";

export const Route = createFileRoute("/sessions/$sessionId")({
  component: SessionDetailPage,
});

function SessionDetailPage() {
  const { sessionId } = Route.useParams();
  const navigate = useNavigate();
  const [offset, setOffset] = useState(0);
  const [tagInput, setTagInput] = useState("");
  const [showTagInput, setShowTagInput] = useState(false);

  const { data, isPending, error } = useSession(sessionId, offset);
  const meta = data?.session;

  const { data: siblings } = useSessions(
    meta ? { project_id: meta.project_id, limit: 20 } : undefined,
  );

  const { data: allTags } = useTags();

  const pinMutation = usePinSession();
  const unpinMutation = useUnpinSession();
  const attachTag = useAttachTag();
  const detachTag = useDetachTag();

  const { data: notes } = useNotes(sessionId);
  const { data: highlights } = useHighlights(sessionId);
  const createNote = useCreateNote();
  const updateNote = useUpdateNote();
  const deleteNote = useDeleteNote();
  const createHighlight = useCreateHighlight();
  const deleteHighlight = useDeleteHighlight();

  const streamRef = useRef<HTMLDivElement | null>(null);

  const handleJumpToMessage = useCallback((messageUuid: string) => {
    const el = streamRef.current?.querySelector<HTMLElement>(
      `[data-message-uuid="${messageUuid}"]`,
    );
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  const handleLoadMore = useCallback(() => {
    if (data?.has_more) setOffset(data.next_offset);
  }, [data]);

  const handleCopyId = useCallback(() => {
    navigator.clipboard.writeText(sessionId);
  }, [sessionId]);

  const handleTogglePin = useCallback(() => {
    if (!meta) return;
    if (meta.pinned) {
      unpinMutation.mutate(sessionId);
    } else {
      pinMutation.mutate(sessionId);
    }
  }, [meta, sessionId, pinMutation, unpinMutation]);

  const handleAddTag = useCallback(() => {
    const name = tagInput.trim();
    if (!name) return;
    attachTag.mutate({ sessionId, name });
    setTagInput("");
    setShowTagInput(false);
  }, [tagInput, sessionId, attachTag]);

  const handleDetachTag = useCallback(
    (tagId: number) => {
      detachTag.mutate({ sessionId, tagId });
    },
    [sessionId, detachTag],
  );

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

  // tags: meta.tags 는 string[] (이름), allTags 에서 tag_id 매핑
  const sessionTagIds = (allTags ?? []).filter((t) =>
    meta.tags.includes(t.name),
  );

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
        <header className="border-b border-outline-variant/30 p-6">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <h2 className="text-md font-bold text-on-surface">
                  {meta.summary || sessionId.slice(0, 8)}
                </h2>
                <span className="font-mono text-xs text-outline" title={sessionId}>
                  {sessionId.slice(0, 8)}
                </span>
                <button
                  onClick={handleCopyId}
                  className="text-outline transition-colors hover:text-primary"
                  title="ID 복사"
                >
                  <Copy size={14} />
                </button>
                {meta.pinned && (
                  <Pin size={14} className="text-primary" />
                )}
              </div>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5 rounded border border-outline-variant/30 bg-surface-container-highest px-2 py-0.5">
                  <Folder size={14} className="text-outline" />
                  <span className="font-mono text-sm text-outline-variant">
                    {shortenPath(meta.decoded_cwd)}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 text-outline">
                  <Calendar size={14} />
                  <span className="text-sm">
                    {meta.started_at.slice(0, 10)}
                  </span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-1.5 rounded border border-outline-variant/20 px-2 py-1">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
              <span className="font-mono text-xs uppercase tracking-tighter text-outline-variant">
                {meta.message_count}개 메시지
              </span>
            </div>
          </div>

          {/* Tags row */}
          <div className="mt-3 flex flex-wrap items-center gap-2">
            {sessionTagIds.map((t) => (
              <span
                key={t.tag_id}
                className="flex items-center gap-1 rounded-xs border border-outline-variant/30 bg-surface-container-highest px-2 py-0.5 font-mono text-xs text-on-surface-variant"
              >
                {t.name}
                <button
                  onClick={() => handleDetachTag(t.tag_id)}
                  className="text-outline transition-colors hover:text-error"
                >
                  <X size={10} />
                </button>
              </span>
            ))}
            {showTagInput ? (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleAddTag();
                }}
                className="flex items-center gap-1"
              >
                <input
                  autoFocus
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onBlur={() => {
                    if (!tagInput.trim()) setShowTagInput(false);
                  }}
                  placeholder="태그 이름"
                  className="w-24 border-b border-outline-variant bg-transparent px-1 py-0.5 font-mono text-xs text-on-surface placeholder:text-outline/50 focus:border-primary focus:outline-none"
                />
              </form>
            ) : (
              <button
                onClick={() => setShowTagInput(true)}
                className="flex items-center gap-1 rounded-xs border border-dashed border-outline-variant/40 px-2 py-0.5 font-mono text-xs text-outline transition-colors hover:border-primary hover:text-primary"
              >
                <Tag size={10} />
                태그
              </button>
            )}
          </div>
        </header>

        {/* Notes */}
        <NotesPanel
          notes={notes ?? []}
          onAdd={(body) => createNote.mutate({ sessionId, body })}
          onUpdate={(noteId, body) =>
            updateNote.mutate({ noteId, sessionId, body })
          }
          onDelete={(noteId) => deleteNote.mutate({ noteId, sessionId })}
          isAdding={createNote.isPending}
        />

        {/* Highlights */}
        <HighlightsPanel
          highlights={highlights ?? []}
          onDelete={(highlightId) =>
            deleteHighlight.mutate({ highlightId, sessionId })
          }
          onJumpToMessage={handleJumpToMessage}
        />

        {/* Messages */}
        <div ref={streamRef} className="flex-1 overflow-y-auto">
          <SessionStream
            messages={data.messages}
            hasMore={data.has_more}
            onLoadMore={handleLoadMore}
          />
        </div>
        <HighlightSelectionToolbar
          containerRef={streamRef}
          onSave={({ text, messageUuid }) =>
            createHighlight.mutate({
              sessionId,
              body: { text, message_uuid: messageUuid, kind: "insight" },
            })
          }
        />

        {/* Footer actions */}
        <footer className="flex items-center border-t border-outline-variant/30 bg-surface-variant/70 p-4 backdrop-blur-md">
          <button
            onClick={handleTogglePin}
            disabled={pinMutation.isPending || unpinMutation.isPending}
            className={`flex items-center gap-2 rounded px-3 py-2 text-sm font-medium transition-all ${
              meta.pinned
                ? "text-primary hover:bg-surface-container-highest"
                : "text-outline hover:bg-surface-container-highest hover:text-on-surface"
            }`}
          >
            {meta.pinned ? <PinOff size={18} /> : <Pin size={18} />}
            {meta.pinned ? "고정 해제" : "고정"}
          </button>
        </footer>
      </section>
    </div>
  );
}
