import { useState } from "react";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { BookOpen, Plus, Search } from "lucide-react";
import { useKnowledgeList } from "~/api/queries";
import { useCreateKnowledge } from "~/api/mutations";
import { timeAgo } from "~/lib/format";

export interface KnowledgeSearch {
  kind?: string;
  q?: string;
  offset?: number;
}

const PAGE_SIZE = 50;

const KIND_LABELS: Record<string, string> = {
  insight: "인사이트",
  prompt: "프롬프트",
  recipe: "레시피",
  snippet: "스니펫",
  question: "질문",
};

const KIND_KEYS = Object.keys(KIND_LABELS);

export const Route = createFileRoute("/knowledge")({
  component: KnowledgePage,
  validateSearch: (search: Record<string, unknown>): KnowledgeSearch => {
    const offsetRaw = Number(search.offset);
    const offset =
      Number.isFinite(offsetRaw) && offsetRaw > 0 ? offsetRaw : undefined;
    const q = typeof search.q === "string" && search.q ? search.q : undefined;
    const kind =
      typeof search.kind === "string" && search.kind ? search.kind : undefined;
    return { kind, q, offset };
  },
});

function KnowledgePage() {
  const { kind, q, offset = 0 } = Route.useSearch();
  const navigate = useNavigate({ from: "/knowledge" });
  const [queryInput, setQueryInput] = useState(q ?? "");
  const createMut = useCreateKnowledge();

  const { data, isPending } = useKnowledgeList({
    kind,
    q,
    limit: PAGE_SIZE,
    offset,
  });

  const submitSearch = (value: string) => {
    const next = value.trim() || undefined;
    navigate({ search: { q: next, kind, offset: undefined } });
  };

  const handleCreate = () => {
    createMut.mutate(
      { title: "새 지식 항목", kind: "insight" },
      {
        onSuccess: (item) => {
          navigate({
            to: "/knowledge/$knowledgeId",
            params: { knowledgeId: String(item.knowledge_id) },
          });
        },
      },
    );
  };

  const items = data?.items ?? [];
  const total = data?.total_count ?? 0;
  const hasNext = data?.next_offset != null;
  const hasPrev = offset > 0;

  return (
    <div className="flex flex-1 flex-col overflow-auto bg-surface-dim">
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-outline-variant/10 px-4 py-2">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            submitSearch(queryInput);
          }}
          className="relative flex-1"
        >
          <Search
            size={14}
            className="absolute left-2 top-1/2 -translate-y-1/2 text-outline"
          />
          <input
            value={queryInput}
            onChange={(e) => setQueryInput(e.target.value)}
            placeholder="지식 검색..."
            className="w-full rounded-sm border border-outline-variant/30 bg-surface py-1.5 pl-7 pr-3 text-sm text-on-surface placeholder:text-outline focus:border-primary focus:outline-none"
          />
        </form>

        <button
          onClick={handleCreate}
          disabled={createMut.isPending}
          className="flex items-center gap-1.5 rounded-sm border border-primary/30 bg-primary/5 px-3 py-1.5 text-sm text-primary transition-colors hover:bg-primary/10"
        >
          <Plus size={14} />
          <span>새 지식</span>
        </button>
      </div>

      {/* Kind filter chips */}
      <div className="flex gap-1.5 border-b border-outline-variant/10 px-4 py-2">
        <button
          onClick={() => navigate({ search: { q, kind: undefined, offset: undefined } })}
          className={`rounded-sm px-2.5 py-1 text-xs transition-colors ${
            !kind
              ? "bg-primary/10 text-primary"
              : "bg-surface-container text-on-surface-variant hover:bg-surface-container-high"
          }`}
        >
          전체
        </button>
        {KIND_KEYS.map((k) => (
          <button
            key={k}
            onClick={() =>
              navigate({
                search: { q, kind: kind === k ? undefined : k, offset: undefined },
              })
            }
            className={`rounded-sm px-2.5 py-1 text-xs transition-colors ${
              kind === k
                ? "bg-primary/10 text-primary"
                : "bg-surface-container text-on-surface-variant hover:bg-surface-container-high"
            }`}
          >
            {KIND_LABELS[k]}
          </button>
        ))}
      </div>

      {/* List */}
      {isPending ? (
        <div className="flex flex-1 items-center justify-center text-outline">
          불러오는 중...
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-3 text-on-surface-variant">
          <BookOpen size={32} className="text-outline-variant/30" />
          <p className="text-sm">지식 항목이 없습니다.</p>
          <p className="text-xs text-outline">
            세션 하이라이트를 승격하거나 직접 생성하세요.
          </p>
        </div>
      ) : (
        <>
          <div className="flex-1 overflow-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 border-b border-outline-variant/20 bg-surface-dim text-xs text-on-surface-variant">
                <tr>
                  <th className="px-4 py-2 text-left font-medium">제목</th>
                  <th className="w-24 px-4 py-2 text-left font-medium">종류</th>
                  <th className="w-32 px-4 py-2 text-right font-medium">수정</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr
                    key={item.knowledge_id}
                    className="border-b border-outline-variant/10 transition-colors hover:bg-surface-container-low"
                  >
                    <td className="px-4 py-2.5">
                      <Link
                        to="/knowledge/$knowledgeId"
                        params={{ knowledgeId: String(item.knowledge_id) }}
                        className="font-medium text-on-surface hover:text-primary"
                      >
                        {item.title}
                      </Link>
                      {item.body && (
                        <p className="mt-0.5 line-clamp-1 text-xs text-outline">
                          {item.body.slice(0, 120)}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-2.5">
                      <span className="rounded-sm bg-surface-container px-2 py-0.5 text-xs text-on-surface-variant">
                        {KIND_LABELS[item.kind] ?? item.kind}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-right text-xs text-outline">
                      {timeAgo(item.updated_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between border-t border-outline-variant/10 px-4 py-2 text-xs text-on-surface-variant">
            <span>총 {total}건</span>
            <div className="flex gap-2">
              {hasPrev && (
                <button
                  onClick={() =>
                    navigate({
                      search: {
                        q,
                        kind,
                        offset: Math.max(0, offset - PAGE_SIZE),
                      },
                    })
                  }
                  className="rounded-sm border border-outline-variant/30 px-2 py-1 hover:bg-surface-container"
                >
                  이전
                </button>
              )}
              {hasNext && (
                <button
                  onClick={() =>
                    navigate({
                      search: { q, kind, offset: data!.next_offset! },
                    })
                  }
                  className="rounded-sm border border-outline-variant/30 px-2 py-1 hover:bg-surface-container"
                >
                  다음
                </button>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
