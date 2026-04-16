import { useState, useMemo } from "react";
import {
  User,
  Bot,
  ChevronRight,
  ChevronDown,
  AlertCircle,
  Terminal,
} from "lucide-react";
import type { MessageItem } from "~/api/queries";
import { MarkdownContent } from "./MarkdownContent";

interface Props {
  messages: MessageItem[];
  hasBefore?: boolean;
  isLoadingEarlier?: boolean;
  onLoadEarlier?: () => void;
  hasMore?: boolean;
}

interface ToolUseEntry {
  id?: string;
  name?: string;
  input?: Record<string, unknown>;
}

interface ToolResultEntry {
  tool_use_id?: string;
  content?: string;
  is_error?: boolean;
}

/** tool_use id → tool_result 매핑 빌드 */
function buildResultMap(messages: MessageItem[]): Map<string, ToolResultEntry> {
  const map = new Map<string, ToolResultEntry>();
  for (const msg of messages) {
    if (!msg.content || !Array.isArray(msg.content)) continue;
    for (const block of msg.content) {
      if (
        typeof block === "object" &&
        block !== null &&
        (block as Record<string, unknown>).type === "tool_result"
      ) {
        const r = block as Record<string, unknown>;
        const id = r.tool_use_id as string | undefined;
        if (id) {
          // content 가 string 이거나 list of blocks 일 수 있음
          let content: string | undefined;
          if (typeof r.content === "string") {
            content = r.content;
          } else if (Array.isArray(r.content)) {
            content = (r.content as Record<string, unknown>[])
              .filter((b) => b.type === "text" && typeof b.text === "string")
              .map((b) => b.text as string)
              .join("\n");
          }
          map.set(id, {
            tool_use_id: id,
            content,
            is_error: r.is_error as boolean | undefined,
          });
        }
      }
    }
  }
  return map;
}

const MAX_RESULT_LINES = 50;
const MAX_RESULT_CHARS = 5000;

/** 결과 텍스트에 마크다운 문법이 포함되어 있는지 간단 휴리스틱 */
function looksLikeMarkdown(text: string): boolean {
  // 헤딩, 볼드, 리스트, 코드블록, 링크 등
  return /^#{1,3}\s/m.test(text) || /\*\*.+\*\*/m.test(text) || /^```/m.test(text) || /^\|.+\|$/m.test(text);
}

function truncateResult(text: string): { text: string; truncated: boolean } {
  const lines = text.split("\n");
  if (lines.length > MAX_RESULT_LINES || text.length > MAX_RESULT_CHARS) {
    const sliced = lines.slice(0, MAX_RESULT_LINES).join("\n");
    return {
      text: sliced.slice(0, MAX_RESULT_CHARS),
      truncated: true,
    };
  }
  return { text, truncated: false };
}

function ToolUseCard({
  tool,
  result,
}: {
  tool: ToolUseEntry;
  result?: ToolResultEntry;
}) {
  const [open, setOpen] = useState(false);
  const name = tool.name ?? "unknown";
  const input = tool.input;
  const hasInput = input && Object.keys(input).length > 0;
  const hasResult = result?.content != null && result.content.length > 0;
  const hasContent = hasInput || hasResult;

  const truncated = useMemo(
    () => (hasResult ? truncateResult(result!.content!) : null),
    [hasResult, result],
  );

  return (
    <div
      className={`rounded border transition-colors hover:border-outline-variant/40 ${
        result?.is_error
          ? "border-error-dim/30 bg-error-dim/5"
          : "border-outline-variant/20 bg-surface-container-lowest"
      }`}
    >
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
          <Terminal size={12} className="text-outline" />
          <code className="font-mono text-sm text-primary-dim">{name}</code>
          {result?.is_error && (
            <span className="flex items-center gap-1 rounded bg-error-dim/20 px-1.5 py-0.5 font-mono text-2xs text-error-dim">
              <AlertCircle size={10} />
              오류
            </span>
          )}
        </div>
        {!open && (
          <span className="px-2 font-mono text-xs text-outline/40">
            {hasContent ? "클릭하여 확장" : "입력 없음"}
          </span>
        )}
      </button>
      {open && hasContent && (
        <div className="space-y-0 border-t border-outline-variant/15">
          {hasInput && (
            <div className="p-3">
              <div className="mb-1 font-mono text-2xs uppercase tracking-wider text-outline/60">
                입력
              </div>
              <pre className="overflow-x-auto font-mono text-xs leading-relaxed text-on-surface-variant">
                {JSON.stringify(input, null, 2)}
              </pre>
            </div>
          )}
          {hasResult && truncated && (
            <div
              className={`p-3 ${hasInput ? "border-t border-outline-variant/10" : ""}`}
            >
              <div className="mb-1 font-mono text-2xs uppercase tracking-wider text-outline/60">
                결과
              </div>
              {looksLikeMarkdown(truncated.text) ? (
                <div className="text-sm">
                  <MarkdownContent content={truncated.text} />
                </div>
              ) : (
                <pre
                  className={`overflow-x-auto font-mono text-xs leading-relaxed ${
                    result?.is_error
                      ? "text-error-dim"
                      : "text-on-surface-variant"
                  }`}
                >
                  {truncated.text}
                </pre>
              )}
              {truncated.truncated && (
                <span className="mt-1 inline-block font-mono text-2xs text-outline/50">
                  … 결과가 잘렸습니다
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/** tool_result 전용 user 메시지인지 판별 */
function isToolResultOnly(msg: MessageItem): boolean {
  if (msg.type !== "user" || msg.text) return false;
  if (!msg.content || !Array.isArray(msg.content)) return false;
  return msg.content.every(
    (b) =>
      typeof b === "object" &&
      b !== null &&
      (b as Record<string, unknown>).type === "tool_result",
  );
}

function MessageBlock({
  msg,
  resultMap,
}: {
  msg: MessageItem;
  resultMap: Map<string, ToolResultEntry>;
}) {
  // tool_result 전용 user 메시지는 숨김 (ToolUseCard 안에서 표시)
  if (isToolResultOnly(msg)) return null;

  if (msg.type === "user") {
    return (
      <article className="flex gap-4" data-message-uuid={msg.uuid ?? undefined}>
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
      <article className="flex gap-4" data-message-uuid={msg.uuid ?? undefined}>
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
                  <ToolUseCard
                    key={t.id ?? i}
                    tool={t}
                    result={t.id ? resultMap.get(t.id) : undefined}
                  />
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

export function SessionStream({
  messages,
  hasBefore,
  isLoadingEarlier,
  onLoadEarlier,
  hasMore,
}: Props) {
  const resultMap = useMemo(() => buildResultMap(messages), [messages]);

  return (
    <div className="space-y-8 p-6">
      {hasBefore && onLoadEarlier && (
        <div className="flex justify-center pb-4">
          <button
            onClick={onLoadEarlier}
            disabled={isLoadingEarlier}
            className="rounded-xs border border-outline-variant bg-surface-container px-4 py-2 font-mono text-sm text-on-surface-variant transition-colors hover:bg-surface-container-high disabled:opacity-50"
          >
            {isLoadingEarlier ? "불러오는 중…" : "이전 대화 불러오기"}
          </button>
        </div>
      )}
      {messages.map((msg, i) => (
        <MessageBlock
          key={msg.uuid ?? i}
          msg={msg}
          resultMap={resultMap}
        />
      ))}
      {hasMore && (
        <div className="flex justify-center pt-4 text-xs text-outline">
          대화가 계속됩니다…
        </div>
      )}
    </div>
  );
}
