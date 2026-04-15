import { useState } from "react";
import { FileOutput } from "lucide-react";
import { shortenPath, timeAgo } from "~/lib/format";
import type { ArtifactRow } from "~/api/queries";

interface Props {
  artifacts: ArtifactRow[];
}

const TOOL_TONE: Record<string, string> = {
  Write: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  Edit: "bg-sky-500/10 text-sky-600 dark:text-sky-400",
  MultiEdit: "bg-violet-500/10 text-violet-600 dark:text-violet-400",
};

export function ArtifactsPanel({ artifacts }: Props) {
  const [expanded, setExpanded] = useState(true);
  const has = artifacts.length > 0;

  return (
    <div className="border-b border-outline-variant/30 px-6 py-3">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-sm font-medium text-on-surface-variant transition-colors hover:text-on-surface"
      >
        <FileOutput size={14} />
        <span>산출물{has && ` (${artifacts.length})`}</span>
      </button>

      {expanded && has && (
        <ul className="mt-2 space-y-1">
          {artifacts.map((a) => (
            <li
              key={a.artifact_id}
              className="group flex items-center gap-2 rounded-sm px-2 py-1 hover:bg-surface-container-low"
            >
              <span
                className={`rounded-xs px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider ${
                  TOOL_TONE[a.tool_name] ?? "bg-outline/10 text-outline"
                }`}
              >
                {a.tool_name}
              </span>
              <span
                className={`flex-1 truncate font-mono text-xs ${
                  a.exists
                    ? "text-on-surface-variant"
                    : "text-outline line-through opacity-60"
                }`}
                title={a.path}
              >
                {shortenPath(a.path)}
              </span>
              <span className="text-xs text-outline opacity-0 transition-opacity group-hover:opacity-100">
                {timeAgo(a.created_at)}
              </span>
            </li>
          ))}
        </ul>
      )}

      {expanded && !has && (
        <p className="mt-2 text-xs text-outline">이 세션에서 생성·수정된 파일이 없어.</p>
      )}
    </div>
  );
}
