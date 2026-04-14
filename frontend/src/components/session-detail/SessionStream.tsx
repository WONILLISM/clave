import { useState } from "react";
import { User, Bot, ChevronRight, ChevronDown } from "lucide-react";
import type { MessageItem } from "~/api/queries";
import { MarkdownContent } from "./MarkdownContent";

interface Props {
  messages: MessageItem[];
  hasMore: boolean;
  onLoadMore: () => void;
}

interface ToolUseEntry {
  id?: string;
  name?: string;
  input?: Record<string, unknown>;
}

function ToolUseCard({ tool }: { tool: ToolUseEntry }) {
  const [open, setOpen] = useState(false);
  const name = tool.name ?? "unknown";
  const input = tool.input;
  const hasInput = input && Object.keys(input).length > 0;

  return (
    <div className="rounded border border-outline-variant/20 bg-surface-container-lowest transition-colors hover:border-outline-variant/40">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between p-2"
      >
        <div className="flex items-center gap-2">
          {open ? (
            <ChevronDown size={14} className="text-primary" />
          ) : (
            <ChevronRight size={14} className="text-primary" />
          )}
          <code className="font-mono text-sm text-primary-dim">{name}</code>
        </div>
        {!open && (
          <span className="px-2 font-mono text-xs text-outline/40">
            {hasInput ? "클릭하여 확장" : "입력 없음"}
          </span>
        )}
      </button>
      {open && hasInput && (
        <div className="border-t border-outline-variant/15 p-3">
          <pre className="overflow-x-auto font-mono text-xs leading-relaxed text-on-surface-variant">
            {JSON.stringify(input, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

function MessageBlock({ msg }: { msg: MessageItem }) {
  if (msg.type === "user") {
    return (
      <article className="flex gap-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded border border-outline-variant/30 bg-surface-container-highest">
          <User size={18} className="text-outline" />
        </div>
        <div className="min-w-0 max-w-2xl space-y-2">
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
    const tools = (msg.tool_use ?? []) as ToolUseEntry[];

    return (
      <article className="flex gap-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded border border-primary/30 bg-primary-container/20">
          <Bot size={18} className="text-primary" />
        </div>
        <div className="min-w-0 max-w-2xl space-y-2">
          <span className="font-mono text-xs uppercase tracking-widest text-primary">
            어시스턴트
          </span>
          <div className="space-y-3">
            {msg.text && <MarkdownContent content={msg.text} />}
            {tools.length > 0 && (
              <div className="space-y-1.5">
                {tools.map((t, i) => (
                  <ToolUseCard key={t.id ?? i} tool={t} />
                ))}
              </div>
            )}
          </div>
        </div>
      </article>
    );
  }

  // other types
  return (
    <article className="flex gap-4 opacity-50">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded border border-outline-variant/30 bg-surface-container-highest">
        <span className="font-mono text-xs text-outline">?</span>
      </div>
      <div className="min-w-0 max-w-2xl">
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
