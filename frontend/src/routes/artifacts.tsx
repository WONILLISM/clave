import { useState } from "react";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Search, ChevronLeft, ChevronRight } from "lucide-react";
import { useArtifactPaths } from "~/api/queries";
import { ArtifactsTable } from "~/components/artifacts/ArtifactsTable";
import { ArtifactSessionsDrawer } from "~/components/artifacts/ArtifactSessionsDrawer";

export interface ArtifactsSearch {
  q?: string;
  offset?: number;
}

const PAGE_SIZE = 50;

export const Route = createFileRoute("/artifacts")({
  component: ArtifactsPage,
  validateSearch: (search: Record<string, unknown>): ArtifactsSearch => {
    const offsetRaw = Number(search.offset);
    const offset =
      Number.isFinite(offsetRaw) && offsetRaw > 0 ? offsetRaw : undefined;
    const q = typeof search.q === "string" && search.q ? search.q : undefined;
    return { q, offset };
  },
});

function ArtifactsPage() {
  const { q, offset = 0 } = Route.useSearch();
  const navigate = useNavigate({ from: "/artifacts" });
  const [queryInput, setQueryInput] = useState(q ?? "");
  const [selectedPath, setSelectedPath] = useState<string | null>(null);

  const { data, isPending, error } = useArtifactPaths({
    limit: PAGE_SIZE,
    offset,
    q,
  });

  const submitSearch = (value: string) => {
    const next = value.trim() || undefined;
    navigate({ search: { q: next, offset: undefined } });
  };

  return (
    <div className="flex flex-1 flex-col overflow-auto bg-surface-dim">
      {/* Filter bar */}
      <div className="flex items-center gap-2 border-b border-outline-variant/10 px-4 py-2">
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
            className="w-64 bg-transparent font-mono text-xs text-on-surface placeholder:text-outline/50 focus:outline-none"
          />
        </form>

        {q && (
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
      {data && data.items.length > 0 && (
        <ArtifactsTable items={data.items} onSelectPath={setSelectedPath} />
      )}

      {/* Pagination */}
      {data && (offset > 0 || data.next_offset != null) && (
        <div className="flex items-center justify-between border-t border-outline-variant/10 px-4 py-2">
          <button
            disabled={offset === 0}
            onClick={() =>
              navigate({
                search: {
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
            disabled={data.next_offset == null}
            onClick={() =>
              navigate({
                search: { q, offset: offset + PAGE_SIZE },
              })
            }
            className="flex items-center gap-1 rounded-xs border border-outline-variant/20 bg-surface-container-high px-2 py-1 font-mono text-xs text-on-surface-variant transition-colors hover:border-primary/50 disabled:cursor-not-allowed disabled:opacity-40"
          >
            다음
            <ChevronRight size={12} />
          </button>
        </div>
      )}

      <ArtifactSessionsDrawer
        path={selectedPath}
        onClose={() => setSelectedPath(null)}
      />
    </div>
  );
}
