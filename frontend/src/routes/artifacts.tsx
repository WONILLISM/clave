import { useState } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Search, ChevronLeft, ChevronRight } from "lucide-react";
import { useArtifacts } from "~/api/queries";
import { ArtifactsTable } from "~/components/artifacts/ArtifactsTable";

type ToolFilter = "Write" | "Edit" | "MultiEdit";

export interface ArtifactsSearch {
  tool?: ToolFilter;
  q?: string;
  offset?: number;
}

const PAGE_SIZE = 50;
const TOOLS: ToolFilter[] = ["Write", "Edit", "MultiEdit"];

export const Route = createFileRoute("/artifacts")({
  component: ArtifactsPage,
  validateSearch: (search: Record<string, unknown>): ArtifactsSearch => {
    const toolRaw = search.tool;
    const tool =
      toolRaw === "Write" || toolRaw === "Edit" || toolRaw === "MultiEdit"
        ? (toolRaw as ToolFilter)
        : undefined;
    const offsetRaw = Number(search.offset);
    const offset = Number.isFinite(offsetRaw) && offsetRaw > 0 ? offsetRaw : undefined;
    const q = typeof search.q === "string" && search.q ? search.q : undefined;
    return { tool, q, offset };
  },
});

function ArtifactsPage() {
  const { tool, q, offset = 0 } = Route.useSearch();
  const navigate = useNavigate({ from: "/artifacts" });
  const [queryInput, setQueryInput] = useState(q ?? "");

  const { data, isPending, error } = useArtifacts({
    limit: PAGE_SIZE,
    offset,
    tool: tool ?? null,
    path_contains: q ?? null,
  });

  const submitSearch = (value: string) => {
    const next = value.trim() || undefined;
    navigate({ search: { tool, q: next, offset: undefined } });
  };

  return (
    <div className="flex flex-1 flex-col overflow-auto bg-surface-dim">
      {/* Filter bar */}
      <div className="flex items-center gap-2 border-b border-outline-variant/10 px-4 py-2">
        {/* Tool filter */}
        <div className="flex items-center gap-1">
          <button
            onClick={() =>
              navigate({ search: { tool: undefined, q, offset: undefined } })
            }
            className={`rounded-xs border px-2 py-1 font-mono text-xs transition-colors ${
              !tool
                ? "border-primary bg-primary/10 text-primary"
                : "border-outline-variant/20 bg-surface-container-high text-on-surface-variant hover:border-primary/50"
            }`}
          >
            전체
          </button>
          {TOOLS.map((t) => (
            <button
              key={t}
              onClick={() =>
                navigate({ search: { tool: t, q, offset: undefined } })
              }
              className={`rounded-xs border px-2 py-1 font-mono text-xs transition-colors ${
                tool === t
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-outline-variant/20 bg-surface-container-high text-on-surface-variant hover:border-primary/50"
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        {/* Path search */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            submitSearch(queryInput);
          }}
          className="flex items-center gap-1 rounded-xs border border-outline-variant/20 bg-surface-container-high px-2 py-1"
        >
          <Search size={12} className="text-outline" />
          <input
            value={queryInput}
            onChange={(e) => setQueryInput(e.target.value)}
            placeholder="경로 포함"
            className="w-48 bg-transparent font-mono text-xs text-on-surface placeholder:text-outline/50 focus:outline-none"
          />
        </form>

        {(tool || q) && (
          <button
            onClick={() => {
              setQueryInput("");
              navigate({ search: {} });
            }}
            className="font-mono text-xs text-outline transition-colors hover:text-error"
          >
            필터 초기화
          </button>
        )}
      </div>

      {/* Content */}
      {isPending && (
        <div className="px-6 py-12 text-center text-on-surface-variant">
          불러오는 중…
        </div>
      )}
      {error && (
        <div className="px-6 py-12 text-center text-error">{String(error)}</div>
      )}
      {data && data.items.length === 0 && (
        <div className="px-6 py-12 text-center text-on-surface-variant">
          산출물이 없어.
        </div>
      )}
      {data && data.items.length > 0 && <ArtifactsTable items={data.items} />}

      {/* Pagination */}
      {data && (offset > 0 || data.next_cursor) && (
        <div className="flex items-center justify-between border-t border-outline-variant/10 px-4 py-2">
          <button
            disabled={offset === 0}
            onClick={() =>
              navigate({
                search: {
                  tool,
                  q,
                  offset: Math.max(0, offset - PAGE_SIZE) || undefined,
                },
              })
            }
            className="flex items-center gap-1 rounded-xs border border-outline-variant/20 bg-surface-container-high px-2 py-1 font-mono text-xs text-on-surface-variant transition-colors hover:border-primary/50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <ChevronLeft size={12} />
            이전
          </button>
          <span className="font-mono text-xs text-outline">
            {offset + 1}–{offset + data.items.length}
          </span>
          <button
            disabled={!data.next_cursor}
            onClick={() =>
              navigate({
                search: { tool, q, offset: offset + PAGE_SIZE },
              })
            }
            className="flex items-center gap-1 rounded-xs border border-outline-variant/20 bg-surface-container-high px-2 py-1 font-mono text-xs text-on-surface-variant transition-colors hover:border-primary/50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            다음
            <ChevronRight size={12} />
          </button>
        </div>
      )}
    </div>
  );
}
