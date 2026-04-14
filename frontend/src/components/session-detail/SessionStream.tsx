import { User, Bot, ChevronRight } from "lucide-react";
import type { MessageItem } from "~/api/queries";

interface Props {
  messages: MessageItem[];
  hasMore: boolean;
  onLoadMore: () => void;
}

function MessageBlock({ msg }: { msg: MessageItem }) {
  if (msg.type === "user") {
    return (
      <article className="flex gap-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded border border-outline-variant/30 bg-surface-container-highest">
          <User size={18} className="text-outline" />
        </div>
        <div className="max-w-2xl space-y-2">
          <span className="font-mono text-xs uppercase tracking-widest text-outline">
            사용자
          </span>
          <p className="whitespace-pre-wrap text-md leading-relaxed text-on-surface">
            {msg.text}
          </p>
        </div>
      </article>
    );
  }

  if (msg.type === "assistant") {
    return (
      <article className="flex gap-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded border border-primary/30 bg-primary-container/20">
          <Bot size={18} className="text-primary" />
        </div>
        <div className="max-w-2xl space-y-2">
          <span className="font-mono text-xs uppercase tracking-widest text-primary">
            어시스턴트
          </span>
          <div className="space-y-3">
            {msg.text && (
              <p className="whitespace-pre-wrap text-md leading-relaxed text-on-surface">
                {msg.text}
              </p>
            )}
            {msg.tool_use && msg.tool_use.length > 0 && (
              <div className="space-y-1">
                {msg.tool_use.map((t, i) => (
                  <div
                    key={i}
                    className="group flex cursor-pointer items-center justify-between rounded border border-outline-variant/20 bg-surface-container-lowest p-2 transition-colors hover:border-outline-variant/50"
                  >
                    <div className="flex items-center gap-3">
                      <ChevronRight
                        size={16}
                        className="text-primary"
                      />
                      <code className="font-mono text-sm text-primary-dim">
                        tool: {(t as Record<string, unknown>).name as string ?? "unknown"} 실행됨
                      </code>
                    </div>
                    <span className="px-2 font-mono text-xs text-outline/30 transition-colors group-hover:text-outline">
                      클릭하여 확장
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </article>
    );
  }

  // other types (attachment, queue-operation, unknown) — 간단히 표시
  return (
    <article className="flex gap-4 opacity-50">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded border border-outline-variant/30 bg-surface-container-highest">
        <span className="font-mono text-xs text-outline">?</span>
      </div>
      <div className="max-w-2xl">
        <span className="font-mono text-xs uppercase tracking-widest text-outline">
          {msg.type}
        </span>
        {msg.text && (
          <p className="mt-1 whitespace-pre-wrap text-sm text-outline">
            {msg.text}
          </p>
        )}
      </div>
    </article>
  );
}

export function SessionStream({ messages, hasMore, onLoadMore }: Props) {
  return (
    <div className="space-y-8 p-6">
      {messages.map((msg, i) => (
        <MessageBlock key={msg.uuid ?? i} msg={msg} />
      ))}
      {hasMore && (
        <div className="flex justify-center pt-4">
          <button
            onClick={onLoadMore}
            className="rounded-xs border border-outline-variant bg-surface-container px-4 py-2 font-mono text-sm text-on-surface-variant transition-colors hover:bg-surface-container-high"
          >
            더 불러오기
          </button>
        </div>
      )}
    </div>
  );
}
