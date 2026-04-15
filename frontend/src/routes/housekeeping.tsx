import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Sparkles } from "lucide-react";
import {
  useHousekeepingScan,
  type HousekeepingCandidateItem,
} from "~/api/queries";
import { CandidatesTable } from "~/components/housekeeping/CandidatesTable";
import { formatBytes } from "~/lib/format";

type CategoryFilter =
  | "all"
  | "stale_session"
  | "empty_project"
  | "orphan_project";

export interface HousekeepingSearch {
  category?: CategoryFilter;
  staleDays?: number;
}

export const Route = createFileRoute("/housekeeping")({
  component: HousekeepingPage,
  validateSearch: (search: Record<string, unknown>): HousekeepingSearch => {
    const validCategories = [
      "all",
      "stale_session",
      "empty_project",
      "orphan_project",
    ];
    const category =
      typeof search.category === "string" &&
      validCategories.includes(search.category)
        ? (search.category as CategoryFilter)
        : undefined;
    const staleDaysRaw = Number(search.staleDays);
    const staleDays =
      Number.isFinite(staleDaysRaw) && staleDaysRaw > 0
        ? staleDaysRaw
        : undefined;
    return { category, staleDays };
  },
});

const STALE_DAYS_OPTIONS = [30, 60, 90, 180] as const;

const CATEGORY_LABELS: Record<CategoryFilter, string> = {
  all: "전체",
  stale_session: "오래된 세션",
  empty_project: "빈 프로젝트",
  orphan_project: "고아 프로젝트",
};

function HousekeepingPage() {
  const { category = "all", staleDays = 90 } = Route.useSearch();
  const navigate = Route.useNavigate();
  const [localStaleDays, setLocalStaleDays] = useState<number>(staleDays);

  const { data, isPending, error } = useHousekeepingScan({
    staleDays: localStaleDays,
  });

  const filteredItems: HousekeepingCandidateItem[] =
    data?.items.filter(
      (item: HousekeepingCandidateItem) =>
        category === "all" || item.category === category,
    ) ?? [];

  const setCategory = (c: CategoryFilter) => {
    navigate({ search: { category: c === "all" ? undefined : c, staleDays: localStaleDays !== 90 ? localStaleDays : undefined } });
  };

  const setStaleDays = (d: number) => {
    setLocalStaleDays(d);
    navigate({ search: { category: category === "all" ? undefined : category, staleDays: d !== 90 ? d : undefined } });
  };

  return (
    <div className="flex flex-1 flex-col overflow-auto bg-surface-dim">
      {/* 헤더 */}
      <div className="border-b border-outline-variant/20 px-6 py-4">
        <div className="flex items-center gap-2 mb-1">
          <Sparkles size={16} className="text-primary" />
          <h1 className="text-base font-semibold text-on-surface">정리소</h1>
        </div>
        <p className="text-xs text-on-surface-variant">
          ~/.claude/ 를 스캔해 정리 후보를 탐지합니다. 탐지만 하며 파일을 변경하지
          않습니다.
        </p>
      </div>

      {/* 건강 요약 바 */}
      {data && (
        <div className="flex items-center gap-4 border-b border-outline-variant/10 bg-surface-container-low px-6 py-3">
          <div className="text-xs text-on-surface-variant">
            <span className="font-semibold text-on-surface">
              {data.items.length}
            </span>{" "}
            개 후보
          </div>
          <div className="h-3 w-px bg-outline-variant/30" />
          {(["stale_session", "empty_project", "orphan_project"] as const).map(
            (cat) =>
              (data.summary[cat] ?? 0) > 0 ? (
                <div key={cat} className="text-xs text-on-surface-variant">
                  {CATEGORY_LABELS[cat]}{" "}
                  <span className="font-semibold text-on-surface">
                    {data.summary[cat]}
                  </span>
                </div>
              ) : null,
          )}
          <div className="h-3 w-px bg-outline-variant/30" />
          <div className="text-xs text-on-surface-variant">
            절감 가능{" "}
            <span className="font-semibold text-on-surface">
              {formatBytes(data.total_size_bytes)}
            </span>
          </div>
          <div className="ml-auto text-2xs text-outline font-mono">
            {data.scanned_at}
          </div>
        </div>
      )}

      {/* 필터 바 */}
      <div className="flex items-center gap-2 border-b border-outline-variant/10 px-4 py-2">
        {/* 카테고리 칩 */}
        <div className="flex gap-1">
          {(
            [
              "all",
              "stale_session",
              "empty_project",
              "orphan_project",
            ] as CategoryFilter[]
          ).map((cat) => {
            const count =
              cat === "all"
                ? (data?.items.length ?? 0)
                : (data?.summary[cat] ?? 0);
            const active = category === cat || (cat === "all" && category === "all");
            return (
              <button
                key={cat}
                onClick={() => setCategory(cat)}
                className={[
                  "rounded-xs border px-2 py-1 font-mono text-xs transition-colors duration-100",
                  active
                    ? "border-primary/60 bg-primary/10 text-primary"
                    : "border-outline-variant/20 bg-surface-container-high text-on-surface-variant hover:border-primary/30 hover:text-on-surface",
                ].join(" ")}
              >
                {CATEGORY_LABELS[cat]}
                {data != null && (
                  <span className="ml-1 opacity-60">{count}</span>
                )}
              </button>
            );
          })}
        </div>

        {/* stale_days 토글 */}
        <div className="ml-auto flex items-center gap-1">
          <span className="text-2xs text-on-surface-variant">오래된 기준</span>
          {STALE_DAYS_OPTIONS.map((d) => (
            <button
              key={d}
              onClick={() => setStaleDays(d)}
              className={[
                "rounded-xs border px-2 py-1 font-mono text-xs transition-colors duration-100",
                localStaleDays === d
                  ? "border-primary/60 bg-primary/10 text-primary"
                  : "border-outline-variant/20 bg-surface-container-high text-on-surface-variant hover:border-primary/30 hover:text-on-surface",
              ].join(" ")}
            >
              {d}일
            </button>
          ))}
        </div>
      </div>

      {/* 콘텐츠 */}
      {isPending && (
        <div className="px-6 py-12 text-center text-on-surface-variant">
          스캔 중…
        </div>
      )}
      {error && (
        <div className="px-6 py-12 text-center text-error">
          {String(error)}
        </div>
      )}
      {data && filteredItems.length === 0 && (
        <div className="px-6 py-12 text-center text-on-surface-variant">
          정리 후보가 없습니다.
        </div>
      )}
      {data && filteredItems.length > 0 && (
        <CandidatesTable items={filteredItems} />
      )}
    </div>
  );
}
