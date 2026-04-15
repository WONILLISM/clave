import { useEffect } from "react";
import { useNavigate } from "@tanstack/react-router";
import { X, Copy } from "lucide-react";
import { useArtifactSessions } from "~/api/queries";
import { shortenPath, timeAgo, baseName } from "~/lib/format";
import { TOOL_TONE } from "./ArtifactsTable";

interface Props {
  path: string | null;
  onClose: () => void;
}

/**
 * 우측 사이드 drawer — 선택된 path 를 건드린 세션 목록.
 * backdrop 클릭 / ESC 로 닫힘.
 */
export function ArtifactSessionsDrawer({ path, onClose }: Props) {
  const navigate = useNavigate();
  const { data, isPending, error } = useArtifactSessions(path);

  useEffect(() => {
    if (!path) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [path, onClose]);

  if (!path) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(path);
  };

  return (
    <>
      {/* backdrop */}
      <div
        onClick={onClose}
        className="fixed inset-0 z-40 bg-scrim/30 backdrop-blur-[1px]"
      />
      {/* panel */}
      <aside
        className="fixed right-0 top-0 z-50 flex h-full w-[420px] flex-col border-l border-outline-variant/30 bg-surface-container shadow-2xl"
        role="dialog"
        aria-label="파일 역참조"
      >
        {/* header */}
        <header className="flex items-start gap-2 border-b border-outline-variant/30 p-4">
          <div className="min-w-0 flex-1">
            <div className="font-mono text-xs text-outline">파일 경로</div>
            <div
              className="mt-1 break-all font-mono text-sm text-on-surface"
              title={path}
            >
              {shortenPath(path)}
            </div>
          </div>
          <button
            onClick={handleCopy}
            className="text-outline transition-colors hover:text-primary"
            title="경로 복사"
          >
            <Copy size={14} />
          </button>
          <button
            onClick={onClose}
            className="text-outline transition-colors hover:text-error"
            title="닫기 (ESC)"
          >
            <X size={16} />
          </button>
        </header>

        {/* body */}
        <div className="flex-1 overflow-y-auto p-4">
          {isPending && (
            <div className="text-center text-sm text-on-surface-variant">
              불러오는 중…
            </div>
          )}
          {error && (
            <div className="text-center text-sm text-error">
              {String(error)}
            </div>
          )}
          {data && data.length === 0 && (
            <div className="text-center text-sm text-on-surface-variant">
              이 경로를 건드린 세션이 없습니다.
            </div>
          )}
          {data && data.length > 0 && (
            <>
              <div className="mb-2 font-mono text-xs uppercase tracking-wider text-on-surface-variant">
                이 파일을 건드린 세션 ({data.length})
              </div>
              <ul className="space-y-2">
                {data.map((s) => (
                  <li key={s.session_id}>
                    <button
                      onClick={() => {
                        navigate({
                          to: "/sessions/$sessionId",
                          params: { sessionId: s.session_id },
                        });
                        onClose();
                      }}
                      className="group flex w-full flex-col gap-1 rounded-sm border border-outline-variant/20 bg-surface-container-low px-3 py-2 text-left transition-colors hover:border-primary/50 hover:bg-surface-container-high"
                    >
                      <div className="flex items-center gap-2">
                        <span
                          className={`shrink-0 rounded-xs px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider ${
                            TOOL_TONE[s.tool_name] ?? "bg-outline/10 text-outline"
                          }`}
                        >
                          {s.tool_name}
                        </span>
                        <span
                          className={`min-w-0 flex-1 truncate text-sm transition-colors group-hover:text-primary ${
                            s.session_summary
                              ? "text-on-surface"
                              : "italic text-on-surface-variant/60"
                          }`}
                        >
                          {s.session_summary || s.session_id.slice(0, 8)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between font-mono text-xs text-outline">
                        <span
                          className="truncate"
                          title={s.decoded_cwd ?? undefined}
                        >
                          {s.decoded_cwd ? baseName(s.decoded_cwd) : "—"}
                        </span>
                        <span>
                          {s.edit_count > 1 && (
                            <span className="mr-2 text-on-surface-variant/70">
                              {s.edit_count}회
                            </span>
                          )}
                          {timeAgo(s.created_at)}
                        </span>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      </aside>
    </>
  );
}
