import { Search, SlidersHorizontal } from "lucide-react";

interface TopNavProps {
  children?: React.ReactNode;
}

export function TopNav({ children }: TopNavProps) {
  return (
    <header className="flex h-10 shrink-0 items-center justify-between gap-4 border-b border-outline-variant bg-surface/80 px-4 backdrop-blur-md">
      <div className="flex flex-1 items-center gap-4">
        {/* Search (데코 — W3 에서 동작) */}
        <div className="flex items-center gap-2 rounded border border-outline-variant/30 bg-surface-container-low px-2 py-1 transition-colors focus-within:border-primary/50">
          <Search size={14} className="text-outline" />
          <input
            type="text"
            placeholder="⌘K 검색..."
            readOnly
            className="w-48 border-none bg-transparent font-mono text-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-0"
          />
        </div>
        {children}
      </div>
      <div className="flex items-center gap-3">
        <button className="text-on-surface/40 transition-opacity hover:text-on-surface">
          <SlidersHorizontal size={18} />
        </button>
      </div>
    </header>
  );
}
