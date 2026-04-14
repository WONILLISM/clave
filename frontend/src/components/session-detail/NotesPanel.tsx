import { useState, useCallback } from "react";
import { StickyNote, Plus, Pencil, Trash2, X, Check } from "lucide-react";
import { timeAgo } from "~/lib/format";
import type { NoteRow } from "~/api/queries";

interface Props {
  notes: NoteRow[];
  onAdd: (body: string) => void;
  onUpdate: (noteId: number, body: string) => void;
  onDelete: (noteId: number) => void;
  isAdding?: boolean;
}

export function NotesPanel({
  notes,
  onAdd,
  onUpdate,
  onDelete,
  isAdding,
}: Props) {
  const [expanded, setExpanded] = useState(true);
  const [showInput, setShowInput] = useState(false);
  const [newBody, setNewBody] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editBody, setEditBody] = useState("");

  const handleAdd = useCallback(() => {
    const body = newBody.trim();
    if (!body) return;
    onAdd(body);
    setNewBody("");
    setShowInput(false);
  }, [newBody, onAdd]);

  const handleStartEdit = useCallback((note: NoteRow) => {
    setEditingId(note.note_id);
    setEditBody(note.body);
  }, []);

  const handleSaveEdit = useCallback(() => {
    if (editingId === null) return;
    const body = editBody.trim();
    if (!body) return;
    onUpdate(editingId, body);
    setEditingId(null);
    setEditBody("");
  }, [editingId, editBody, onUpdate]);

  const handleCancelEdit = useCallback(() => {
    setEditingId(null);
    setEditBody("");
  }, []);

  const hasNotes = notes.length > 0;

  return (
    <div className="border-b border-outline-variant/30 px-6 py-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-2 text-sm font-medium text-on-surface-variant transition-colors hover:text-on-surface"
        >
          <StickyNote size={14} />
          <span>
            메모{hasNotes && ` (${notes.length})`}
          </span>
        </button>
        <button
          onClick={() => {
            setShowInput(true);
            setExpanded(true);
          }}
          className="flex items-center gap-1 rounded-xs px-2 py-0.5 text-xs text-outline transition-colors hover:text-primary"
        >
          <Plus size={12} />
          추가
        </button>
      </div>

      {/* Body */}
      {expanded && (
        <div className="mt-2 space-y-2">
          {/* New note input */}
          {showInput && (
            <div className="rounded-sm border border-outline-variant/30 bg-surface-container-low p-2">
              <textarea
                autoFocus
                value={newBody}
                onChange={(e) => setNewBody(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                    handleAdd();
                  }
                  if (e.key === "Escape") {
                    setShowInput(false);
                    setNewBody("");
                  }
                }}
                placeholder="메모 입력… (Cmd+Enter로 저장)"
                rows={2}
                className="w-full resize-none bg-transparent text-sm text-on-surface placeholder:text-outline/50 focus:outline-none"
              />
              <div className="mt-1 flex items-center justify-end gap-2">
                <button
                  onClick={() => {
                    setShowInput(false);
                    setNewBody("");
                  }}
                  className="rounded-xs px-2 py-0.5 text-xs text-outline transition-colors hover:text-on-surface"
                >
                  취소
                </button>
                <button
                  onClick={handleAdd}
                  disabled={!newBody.trim() || isAdding}
                  className="rounded-xs bg-primary/10 px-2 py-0.5 text-xs text-primary transition-colors hover:bg-primary/20 disabled:opacity-40"
                >
                  저장
                </button>
              </div>
            </div>
          )}

          {/* Note list */}
          {notes.map((note) => (
            <div
              key={note.note_id}
              className="group rounded-sm border border-outline-variant/20 bg-surface-container-low px-3 py-2"
            >
              {editingId === note.note_id ? (
                /* Edit mode */
                <div>
                  <textarea
                    autoFocus
                    value={editBody}
                    onChange={(e) => setEditBody(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                        handleSaveEdit();
                      }
                      if (e.key === "Escape") handleCancelEdit();
                    }}
                    rows={2}
                    className="w-full resize-none bg-transparent text-sm text-on-surface focus:outline-none"
                  />
                  <div className="mt-1 flex items-center justify-end gap-2">
                    <button
                      onClick={handleCancelEdit}
                      className="rounded-xs p-1 text-outline transition-colors hover:text-on-surface"
                    >
                      <X size={12} />
                    </button>
                    <button
                      onClick={handleSaveEdit}
                      disabled={!editBody.trim()}
                      className="rounded-xs p-1 text-primary transition-colors hover:text-primary/80 disabled:opacity-40"
                    >
                      <Check size={12} />
                    </button>
                  </div>
                </div>
              ) : (
                /* View mode */
                <div>
                  <p className="whitespace-pre-wrap text-sm text-on-surface">
                    {note.body}
                  </p>
                  <div className="mt-1 flex items-center justify-between">
                    <span className="text-xs text-outline">
                      {timeAgo(note.created_at)}
                      {note.updated_at !== note.created_at && " (수정됨)"}
                    </span>
                    <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                      <button
                        onClick={() => handleStartEdit(note)}
                        className="rounded-xs p-1 text-outline transition-colors hover:text-primary"
                      >
                        <Pencil size={12} />
                      </button>
                      <button
                        onClick={() => onDelete(note.note_id)}
                        className="rounded-xs p-1 text-outline transition-colors hover:text-error"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
