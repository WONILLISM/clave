import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { ArrowLeft, Pencil, Trash2, Check, X } from "lucide-react";
import type { KnowledgeDetailResponse } from "~/api/queries";
import { useUpdateKnowledge, useDeleteKnowledge } from "~/api/mutations";
import { timeAgo } from "~/lib/format";
import { KnowledgeLinkPanel } from "./KnowledgeLinkPanel";

const KIND_LABELS: Record<string, string> = {
  insight: "인사이트",
  prompt: "프롬프트",
  recipe: "레시피",
  snippet: "스니펫",
  question: "질문",
};

interface Props {
  data: KnowledgeDetailResponse;
}

export function KnowledgeDetail({ data }: Props) {
  const { item, links = [], backlinks = [] } = data;
  const navigate = useNavigate();
  const updateMut = useUpdateKnowledge();
  const deleteMut = useDeleteKnowledge();

  const [editingTitle, setEditingTitle] = useState(false);
  const [titleDraft, setTitleDraft] = useState(item.title);
  const [editingBody, setEditingBody] = useState(false);
  const [bodyDraft, setBodyDraft] = useState(item.body);

  const handleSaveTitle = () => {
    if (titleDraft.trim() && titleDraft !== item.title) {
      updateMut.mutate({ knowledgeId: item.knowledge_id, title: titleDraft.trim() });
    }
    setEditingTitle(false);
  };

  const handleSaveBody = () => {
    if (bodyDraft !== item.body) {
      updateMut.mutate({ knowledgeId: item.knowledge_id, body: bodyDraft });
    }
    setEditingBody(false);
  };

  const handleDelete = () => {
    if (!confirm("이 지식 항목을 삭제하시겠습니까?")) return;
    deleteMut.mutate(item.knowledge_id, {
      onSuccess: () => navigate({ to: "/knowledge" }),
    });
  };

  return (
    <div className="flex flex-1 flex-col overflow-auto bg-surface-dim">
      {/* Top bar */}
      <div className="flex items-center gap-3 border-b border-outline-variant/10 px-4 py-2">
        <button
          onClick={() => navigate({ to: "/knowledge" })}
          className="rounded-sm p-1 text-on-surface-variant transition-colors hover:bg-surface-container hover:text-on-surface"
          title="목록으로"
        >
          <ArrowLeft size={16} />
        </button>
        <div className="flex-1" />
        <button
          onClick={handleDelete}
          disabled={deleteMut.isPending}
          className="flex items-center gap-1.5 rounded-sm px-2.5 py-1 text-xs text-error transition-colors hover:bg-error/10"
        >
          <Trash2 size={12} />
          <span>삭제</span>
        </button>
      </div>

      <div className="mx-auto w-full max-w-2xl space-y-6 px-6 py-6">
        {/* Title */}
        <div className="group">
          {editingTitle ? (
            <div className="flex items-center gap-2">
              <input
                value={titleDraft}
                onChange={(e) => setTitleDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSaveTitle();
                  if (e.key === "Escape") {
                    setTitleDraft(item.title);
                    setEditingTitle(false);
                  }
                }}
                autoFocus
                className="flex-1 border-b border-primary bg-transparent text-lg font-bold text-on-surface outline-none"
              />
              <button onClick={handleSaveTitle} className="rounded-sm p-1 text-primary hover:bg-primary/10">
                <Check size={14} />
              </button>
              <button
                onClick={() => { setTitleDraft(item.title); setEditingTitle(false); }}
                className="rounded-sm p-1 text-outline hover:bg-surface-container"
              >
                <X size={14} />
              </button>
            </div>
          ) : (
            <div className="flex items-start gap-2">
              <h1 className="flex-1 text-lg font-bold text-on-surface">{item.title}</h1>
              <button
                onClick={() => setEditingTitle(true)}
                className="rounded-sm p-1 text-outline opacity-0 transition-opacity hover:text-on-surface group-hover:opacity-100"
              >
                <Pencil size={12} />
              </button>
            </div>
          )}
        </div>

        {/* Meta */}
        <div className="flex flex-wrap items-center gap-2 text-xs text-outline">
          <span className="rounded-sm bg-surface-container px-2 py-0.5 text-on-surface-variant">
            {KIND_LABELS[item.kind] ?? item.kind}
          </span>
          {item.source_type && (
            <span className="text-outline-variant">
              출처: {item.source_type} #{item.source_id}
            </span>
          )}
          <span className="ml-auto">{timeAgo(item.updated_at)}</span>
        </div>

        {/* Body */}
        <div className="group">
          {editingBody ? (
            <div className="space-y-2">
              <textarea
                value={bodyDraft}
                onChange={(e) => setBodyDraft(e.target.value)}
                rows={10}
                autoFocus
                className="w-full rounded-sm border border-outline-variant/30 bg-surface p-3 text-sm text-on-surface outline-none focus:border-primary"
              />
              <div className="flex gap-2">
                <button
                  onClick={handleSaveBody}
                  className="rounded-sm border border-primary/30 bg-primary/5 px-3 py-1 text-xs text-primary hover:bg-primary/10"
                >
                  저장
                </button>
                <button
                  onClick={() => { setBodyDraft(item.body); setEditingBody(false); }}
                  className="rounded-sm px-3 py-1 text-xs text-outline hover:bg-surface-container"
                >
                  취소
                </button>
              </div>
            </div>
          ) : (
            <div
              onClick={() => setEditingBody(true)}
              className="cursor-text rounded-sm border border-transparent px-3 py-3 text-sm leading-relaxed text-on-surface transition-colors hover:border-outline-variant/20 hover:bg-surface-container-low"
            >
              {item.body ? (
                <p className="whitespace-pre-wrap">{item.body}</p>
              ) : (
                <p className="text-outline">내용을 입력하세요...</p>
              )}
            </div>
          )}
        </div>

        {/* Links */}
        <KnowledgeLinkPanel
          knowledgeId={item.knowledge_id}
          links={links}
          backlinks={backlinks}
        />
      </div>
    </div>
  );
}
