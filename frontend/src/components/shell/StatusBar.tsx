import { useHealth } from "~/api/queries";

export function StatusBar() {
  const { data: health } = useHealth();

  return (
    <footer className="flex h-6 shrink-0 items-center justify-between border-t border-outline-variant/10 bg-surface-container px-4 font-mono text-2xs text-outline">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <span
            className={`h-1.5 w-1.5 rounded-full ${health ? "bg-emerald-500" : "bg-outline-variant"}`}
          />
          <span className="uppercase tracking-tighter">
            {health ? "시스템: 준비됨" : "오프라인"}
          </span>
        </div>
        {health && (
          <>
            <div className="h-3 w-px bg-outline-variant" />
            <span>세션: {health.indexed_sessions}개</span>
          </>
        )}
      </div>
      <div className="flex items-center gap-4">
        <span className="uppercase tracking-tighter">동기화됨</span>
      </div>
    </footer>
  );
}
