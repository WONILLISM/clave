import { useState } from "react";
import { Star, Trash2 } from "lucide-react";
import { timeAgo } from "~/lib/format";
import type { HighlightRow } from "~/api/queries";

interface Props {
  highlights: HighlightRow[];
  onDelete: (highlightId: number) => void;
  /** 항목 클릭 시 해당 메시지로 스크롤 */
  onJumpToMessage: (messageUuid: string) => void;
}

export function HighlightsPanel({ highlights, onDelete, onJumpToMessage }: Props) {
  const [expanded, setExpanded] = useState(true);
  const has = highlights.length > 0;

  return (
    <div className="border-b border-outline-variant/30 px-6 py-3">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-sm font-medium text-on-surface-variant transition-colors hover:text-on-surface"
      >
        <Star size={14} />
        <span>하이라이트{has && ` (${highlights.length})`}</span>
      </button>

      {expanded && has && (
        <ul className="mt-2 max-h-60 space-y-1.5 overflow-y-auto">
          {highlights.map((h) => (
            <li
              key={h.highlight_id}
              className="group flex items-start gap-2 rounded-sm border-l-2 border-primary/40 bg-surface-container-low px-3 py-2"
            >
              <button
                onClick={() => {
                  if (h.message_uuid) onJumpToMessage(h.message_uuid);
                }}
                disabled={!h.message_uuid}
                className="min-w-0 flex-1 text-left disabled:cursor-default"
                title={h.message_uuid ? "메시지로 점프" : ""}
              >
                <p className="line-clamp-3 whitespace-pre-wrap text-sm text-on-surface">
                  {h.text}
                </p>
                <span className="mt-1 inline-block text-xs text-outline">
                  {timeAgo(h.created_at)}
                </span>
              </button>
              <button
                onClick={() => onDelete(h.highlight_id)}
                className="rounded-xs p-1 text-outline opacity-0 transition-opacity hover:text-error group-hover:opacity-100"
                title="삭제"
              >
                <Trash2 size={12} />
              </button>
            </li>
          ))}
        </ul>
      )}

      {expanded && !has && (
        <p className="mt-2 text-xs text-outline">
          메시지에서 텍스트를 선택해 저장해보자.
        </p>
      )}
    </div>
  );
}
