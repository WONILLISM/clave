import { useState, useCallback, useRef, useMemo, useEffect } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import {
  Copy,
  Folder,
  Calendar,
  Pin,
  PinOff,
  Tag,
  X,
  AlertCircle,
  ArrowLeft,
  Trash2,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import {
  useSession,
  useSessions,
  useTags,
  useNotes,
  useHighlights,
} from "~/api/queries";
import type { SessionDetailResponse } from "~/api/queries";
import { api } from "~/api/client";
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
  useDeleteSession,
} from "~/api/mutations";
import { ApiError } from "~/api/client";
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
  const [tagInput, setTagInput] = useState("");
  const [showTagInput, setShowTagInput] = useState(false);

  // 최신 메시지부터 로드 (from_end=true).
  const { data, isPending, error } = useSession(sessionId, 0, 200, true);
  const meta = data?.session;

  // 이전 대화 청크들 (위로 확장).
  const [earlierChunks, setEarlierChunks] = useState<
    import("~/api/queries").MessageItem[][]
  >([]);
  const [earlierOffset, setEarlierOffset] = useState<number | null>(null);
  const loadedOffsets = useRef(new Set<number>());

  // earlierOffset이 null이 아닐 때만 쿼리 실행.
  const earlierQuery = useQuery({
    queryKey: ["session", sessionId, earlierOffset, false],
    queryFn: () =>
      api<SessionDetailResponse>(
        `/api/sessions/${sessionId}?offset=${earlierOffset}&limit=200`,
      ),
    enabled: earlierOffset !== null,
  });

  // 이전 청크 데이터 도착 시 누적.
  useEffect(() => {
    if (
      earlierQuery.data &&
      earlierOffset !== null &&
      !loadedOffsets.current.has(earlierOffset)
    ) {
      loadedOffsets.current.add(earlierOffset);
      setEarlierChunks((prev) => [earlierQuery.data!.messages, ...prev]);
    }
  }, [earlierQuery.data, earlierOffset]);

  // sessionId 바뀌면 이전 대화 초기화.
  useEffect(() => {
    setEarlierChunks([]);
    setEarlierOffset(null);
    loadedOffsets.current = new Set();
  }, [sessionId]);

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
  const deleteSession = useDeleteSession();

  const streamRef = useRef<HTMLDivElement | null>(null);

  // 초기 로딩 완료 시 스크롤을 맨 아래로.
  const didScrollToBottom = useRef(false);
  useEffect(() => {
    if (data && !didScrollToBottom.current && streamRef.current) {
      streamRef.current.scrollTop = streamRef.current.scrollHeight;
      didScrollToBottom.current = true;
    }
  }, [data]);

  // 세션이 바뀌면 스크롤 플래그 리셋.
  useEffect(() => {
    didScrollToBottom.current = false;
  }, [sessionId]);

  const handleJumpToMessage = useCallback((messageUuid: string) => {
    const el = streamRef.current?.querySelector<HTMLElement>(
      `[data-message-uuid="${messageUuid}"]`,
    );
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  // 현재 보이는 첫 offset 계산: data가 from_end 로딩이므로 실제 offset 추적.
  const currentStartOffset = useMemo(() => {
    if (!data) return 0;
    const msgCount = data.messages.length;
    // from_end 응답: next_offset = effective_offset + consumed
    return Math.max(0, data.next_offset - msgCount);
  }, [data]);

  // 가장 앞쪽에 로드된 offset 추적.
  const lowestLoadedOffset = useMemo(() => {
    if (loadedOffsets.current.size > 0) {
      return Math.min(...loadedOffsets.current);
    }
    return currentStartOffset;
  }, [currentStartOffset, earlierChunks]); // earlierChunks 변경 시 재계산

  const hasBefore = lowestLoadedOffset > 0;

  const handleLoadEarlier = useCallback(() => {
    const newOffset = Math.max(0, lowestLoadedOffset - 200);
    if (newOffset < lowestLoadedOffset) {
      setEarlierOffset(newOffset);
    }
  }, [lowestLoadedOffset]);

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
    const is410 = error instanceof ApiError && error.status === 410;
    if (is410) {
      return (
        <section
          role="region"
          aria-label="사라진 세션"
          className="flex flex-1 flex-col bg-surface-container"
        >
          <header className="space-y-3 border-b border-outline-variant/30 p-6">
            <span
              role="status"
              aria-live="polite"
              className="inline-flex items-center gap-1 rounded-xs bg-error/10 px-1.5 py-0.5 font-mono text-2xs uppercase tracking-wider text-error"
            >
              <AlertCircle size={12} />
              원본 없음
            </span>
            <div className="flex items-center gap-2">
              <h2
                className="font-mono text-md text-on-surface"
                title={sessionId}
              >
                {sessionId}
              </h2>
              <button
                onClick={handleCopyId}
                className="text-outline transition-colors hover:text-primary focus-visible:text-primary focus-visible:outline-none"
                title="ID 복사"
              >
                <Copy size={14} />
              </button>
            </div>
            <p className="text-xs text-on-surface-variant">
              overlay 메타만 남음 · 스캔 DB 에서만 흔적 확인 가능
            </p>
          </header>

          <div className="flex-1 overflow-y-auto px-6 py-12">
            <p className="mx-auto max-w-md text-md text-on-surface">
              이 세션의 jsonl 원본이{" "}
              <code className="font-mono text-sm text-on-surface-variant">
                ~/.claude/
              </code>
              에서 사라졌습니다. overlay 에 메타만 남은 흔적입니다.
            </p>
            <div
              id="delete-hint"
              className="mx-auto mt-6 max-w-md rounded-sm border border-outline-variant/30 bg-surface-container-low p-4 text-xs text-on-surface-variant"
            >
              <div className="mb-2 font-mono text-2xs uppercase tracking-wider text-outline">
                발생 원인
              </div>
              <ul className="list-disc space-y-1 pl-4 marker:text-outline">
                <li>
                  다른 도구로{" "}
                  <code className="font-mono">~/.claude/</code> 를 직접 정리
                </li>
                <li>Claude Code 가 파일 이름을 바꿈</li>
                <li>디스크 복구·이전 중 손실</li>
              </ul>
            </div>
          </div>

          <footer className="flex items-center justify-between border-t border-outline-variant/30 bg-surface-variant/70 p-4 backdrop-blur-md">
            <button
              onClick={() => navigate({ to: "/sessions" })}
              className="flex items-center gap-2 rounded-sm px-3 py-2 text-sm text-on-surface-variant transition-colors hover:bg-surface-container-highest hover:text-on-surface focus-visible:bg-surface-container-highest focus-visible:outline-none"
            >
              <ArrowLeft size={16} />
              세션 목록으로
            </button>
            <button
              disabled={deleteSession.isPending}
              aria-describedby="delete-hint"
              onClick={() => {
                if (!confirm("정말 삭제하시겠어요? 복원할 수 없습니다."))
                  return;
                deleteSession.mutate(sessionId, {
                  onSuccess: () => navigate({ to: "/sessions" }),
                });
              }}
              className="flex items-center gap-2 rounded-sm border border-error/40 bg-error/10 px-3 py-2 text-sm font-medium text-error transition-colors hover:bg-error/20 focus-visible:bg-error/20 focus-visible:outline-none disabled:opacity-50"
            >
              <Trash2 size={16} />
              {deleteSession.isPending ? "지우는 중…" : "흔적 지우기"}
            </button>
          </footer>
        </section>
      );
    }
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
            messages={[...earlierChunks.flat(), ...data.messages]}
            hasBefore={hasBefore}
            isLoadingEarlier={earlierQuery.isPending && earlierOffset !== null}
            onLoadEarlier={handleLoadEarlier}
            hasMore={data.has_more}
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
