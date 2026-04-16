import { useState } from "react";
import { Link } from "@tanstack/react-router";
import {
  ArrowRight,
  ArrowLeft,
  Link2,
  Plus,
  Search,
  Trash2,
  X,
} from "lucide-react";
import type { KnowledgeLinkRow, KnowledgeRow } from "~/api/queries";
import { useKnowledgeList } from "~/api/queries";
import {
  useCreateKnowledgeLink,
  useDeleteKnowledgeLink,
} from "~/api/mutations";

const RELATION_LABELS: Record<string, string> = {
  related: "관련",
  derives_from: "유래",
  refines: "개선",
  contradicts: "반박",
};

const NODE_TYPE_LABELS: Record<string, string> = {
  knowledge: "지식",
  session: "세션",
  highlight: "하이라이트",
  note: "노트",
};

interface Props {
  knowledgeId: number;
  links: KnowledgeLinkRow[];
  backlinks: KnowledgeLinkRow[];
}

export function KnowledgeLinkPanel({
  knowledgeId,
  links,
  backlinks,
}: Props) {
  const [showAdd, setShowAdd] = useState(false);

  return (
    <div className="space-y-4">
      {/* Links (outgoing) */}
      <div>
        <div className="mb-2 flex items-center gap-2">
          <Link2 size={14} className="text-on-surface-variant" />
          <span className="text-sm font-medium text-on-surface-variant">
            링크 ({links.length})
          </span>
          <button
            onClick={() => setShowAdd(!showAdd)}
            className="ml-auto rounded-sm p-1 text-outline transition-colors hover:bg-surface-container hover:text-on-surface"
            title="링크 추가"
          >
            <Plus size={12} />
          </button>
        </div>

        {showAdd && (
          <AddLinkSearch
            knowledgeId={knowledgeId}
            onClose={() => setShowAdd(false)}
          />
        )}

        {links.length > 0 ? (
          <ul className="space-y-1">
            {links.map((lnk) => (
              <LinkItem
                key={lnk.link_id}
                link={lnk}
                knowledgeId={knowledgeId}
                direction="out"
              />
            ))}
          </ul>
        ) : (
          !showAdd && (
            <p className="text-xs text-outline">연결된 항목이 없습니다.</p>
          )
        )}
      </div>

      {/* Backlinks (incoming) */}
      {backlinks.length > 0 && (
        <div>
          <div className="mb-2 flex items-center gap-2">
            <ArrowLeft size={14} className="text-on-surface-variant" />
            <span className="text-sm font-medium text-on-surface-variant">
              역링크 ({backlinks.length})
            </span>
          </div>
          <ul className="space-y-1">
            {backlinks.map((lnk) => (
              <LinkItem
                key={lnk.link_id}
                link={lnk}
                knowledgeId={knowledgeId}
                direction="in"
              />
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function LinkItem({
  link,
  knowledgeId,
  direction,
}: {
  link: KnowledgeLinkRow;
  knowledgeId: number;
  direction: "out" | "in";
}) {
  const deleteMut = useDeleteKnowledgeLink();
  const targetType = direction === "out" ? link.to_type : link.from_type;
  const targetId = direction === "out" ? link.to_id : link.from_id;

  const isKnowledgeTarget = targetType === "knowledge";
  const label = `${NODE_TYPE_LABELS[targetType] ?? targetType} #${targetId}`;

  return (
    <li className="group flex items-center gap-2 rounded-sm bg-surface-container-low px-3 py-1.5 text-sm">
      {direction === "out" ? (
        <ArrowRight size={12} className="text-outline" />
      ) : (
        <ArrowLeft size={12} className="text-outline" />
      )}
      <span className="rounded-sm bg-surface-container px-1.5 py-0.5 text-xs text-on-surface-variant">
        {RELATION_LABELS[link.relation] ?? link.relation}
      </span>
      {isKnowledgeTarget ? (
        <Link
          to="/knowledge/$knowledgeId"
          params={{ knowledgeId: targetId }}
          className="flex-1 truncate text-on-surface hover:text-primary"
        >
          {label}
        </Link>
      ) : targetType === "session" ? (
        <Link
          to="/sessions/$sessionId"
          params={{ sessionId: targetId }}
          className="flex-1 truncate text-on-surface hover:text-primary"
        >
          {label}
        </Link>
      ) : (
        <span className="flex-1 truncate text-on-surface">{label}</span>
      )}
      <button
        onClick={() =>
          deleteMut.mutate({ linkId: link.link_id, knowledgeId })
        }
        className="rounded-sm p-0.5 text-outline opacity-0 transition-opacity hover:text-error group-hover:opacity-100"
        title="링크 삭제"
      >
        <Trash2 size={12} />
      </button>
    </li>
  );
}

function AddLinkSearch({
  knowledgeId,
  onClose,
}: {
  knowledgeId: number;
  onClose: () => void;
}) {
  const [q, setQ] = useState("");
  const { data } = useKnowledgeList({ q: q.length >= 2 ? q : undefined, limit: 10 });
  const createLink = useCreateKnowledgeLink();

  const results = (data?.items ?? []).filter(
    (it: KnowledgeRow) => it.knowledge_id !== knowledgeId,
  );

  const handleSelect = (target: KnowledgeRow) => {
    createLink.mutate(
      {
        knowledgeId,
        from_type: "knowledge",
        from_id: String(knowledgeId),
        to_type: "knowledge",
        to_id: String(target.knowledge_id),
        relation: "related",
      },
      { onSuccess: () => onClose() },
    );
  };

  return (
    <div className="mb-3 rounded-sm border border-outline-variant/30 bg-surface p-2">
      <div className="flex items-center gap-2">
        <Search size={12} className="text-outline" />
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="연결할 지식 검색..."
          autoFocus
          className="flex-1 bg-transparent text-sm text-on-surface outline-none placeholder:text-outline"
        />
        <button
          onClick={onClose}
          className="rounded-sm p-0.5 text-outline hover:text-on-surface"
        >
          <X size={12} />
        </button>
      </div>
      {q.length >= 2 && results.length > 0 && (
        <ul className="mt-2 max-h-40 space-y-0.5 overflow-y-auto">
          {results.map((it: KnowledgeRow) => (
            <li key={it.knowledge_id}>
              <button
                onClick={() => handleSelect(it)}
                className="w-full rounded-sm px-2 py-1 text-left text-sm text-on-surface transition-colors hover:bg-surface-container-low"
              >
                {it.title}
              </button>
            </li>
          ))}
        </ul>
      )}
      {q.length >= 2 && results.length === 0 && (
        <p className="mt-2 text-xs text-outline">검색 결과가 없습니다.</p>
      )}
    </div>
  );
}
