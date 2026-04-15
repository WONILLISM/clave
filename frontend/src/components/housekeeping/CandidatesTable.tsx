import { useNavigate } from "@tanstack/react-router";
import type { HousekeepingCandidateItem } from "~/api/queries";
import { formatBytes, timeAgo } from "~/lib/format";

// 카테고리별 색상 톤 맵
const CATEGORY_TONE: Record<
  HousekeepingCandidateItem["category"],
  { badge: string; label: string }
> = {
  stale_session: {
    badge:
      "bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20",
    label: "오래된 세션",
  },
  empty_project: {
    badge:
      "bg-slate-500/10 text-slate-600 dark:text-slate-400 border border-slate-500/20",
    label: "빈 프로젝트",
  },
  orphan_project: {
    badge:
      "bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20",
    label: "고아 프로젝트",
  },
};

interface CandidatesTableProps {
  items: HousekeepingCandidateItem[];
}

export function CandidatesTable({ items }: CandidatesTableProps) {
  const navigate = useNavigate();

  const handleRowClick = (item: HousekeepingCandidateItem) => {
    if (item.category === "stale_session") {
      navigate({ to: "/sessions/$sessionId", params: { sessionId: item.entity_id } });
    }
    // empty_project / orphan_project — no-op (MVP-0)
  };

  return (
    <div className="overflow-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-outline-variant/20 text-left">
            <th className="px-4 py-2 font-medium text-on-surface-variant text-xs uppercase tracking-wider">
              분류
            </th>
            <th className="px-4 py-2 font-medium text-on-surface-variant text-xs uppercase tracking-wider">
              이름
            </th>
            <th className="px-4 py-2 font-medium text-on-surface-variant text-xs uppercase tracking-wider">
              사유
            </th>
            <th className="px-4 py-2 font-medium text-on-surface-variant text-xs uppercase tracking-wider text-right">
              크기
            </th>
            <th className="px-4 py-2 font-medium text-on-surface-variant text-xs uppercase tracking-wider">
              마지막 활동
            </th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const tone = CATEGORY_TONE[item.category];
            const isClickable = item.category === "stale_session";
            return (
              <tr
                key={`${item.category}-${item.entity_id}`}
                onClick={() => handleRowClick(item)}
                className={[
                  "border-b border-outline-variant/10 transition-colors duration-100",
                  isClickable
                    ? "cursor-pointer hover:bg-surface-container-low"
                    : "cursor-default",
                ].join(" ")}
              >
                <td className="px-4 py-2.5">
                  <span
                    className={[
                      "inline-block rounded-xs px-1.5 py-0.5 font-mono text-2xs",
                      tone.badge,
                    ].join(" ")}
                  >
                    {tone.label}
                  </span>
                </td>
                <td className="px-4 py-2.5 max-w-[240px] truncate font-mono text-xs text-on-surface">
                  {item.display_name}
                </td>
                <td className="px-4 py-2.5 max-w-[320px] truncate text-xs text-on-surface-variant">
                  {item.reason}
                </td>
                <td className="px-4 py-2.5 text-right font-mono text-xs text-on-surface-variant tabular-nums">
                  {formatBytes(item.size_bytes)}
                </td>
                <td className="px-4 py-2.5 text-xs text-on-surface-variant">
                  {item.last_activity ? timeAgo(item.last_activity) : "—"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
