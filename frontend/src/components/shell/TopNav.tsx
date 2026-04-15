import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "@tanstack/react-router";
import { Moon, Search, Sun } from "lucide-react";
import { useSearch } from "../../api/queries";
import { timeAgo, baseName } from "../../lib/format";

interface TopNavProps {
  children?: React.ReactNode;
}

function getInitialTheme(): "dark" | "light" {
  if (typeof window === "undefined") return "dark";
  const stored = localStorage.getItem("theme");
  if (stored === "light" || stored === "dark") return stored;
  return "dark"; // default dark-first
}

export function TopNav({ children }: TopNavProps) {
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [theme, setTheme] = useState<"dark" | "light">(getInitialTheme);
  const navigate = useNavigate();
  const wrapperRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [dropdownPos, setDropdownPos] = useState({ top: 0, left: 0 });

  // Sync theme class on <html>
  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove("dark", "light");
    root.classList.add(theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));
  }, []);

  // Debounce input → 300ms
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQuery(query), 300);
    return () => clearTimeout(t);
  }, [query]);

  const { data, isFetching } = useSearch(debouncedQuery);

  // Position dropdown below input
  useEffect(() => {
    if (open && wrapperRef.current) {
      const rect = wrapperRef.current.getBoundingClientRect();
      setDropdownPos({ top: rect.bottom + 4, left: rect.left });
    }
  }, [open, debouncedQuery]);

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      const target = e.target as Node;
      if (wrapperRef.current?.contains(target)) return;
      // Check if clicking inside the portal dropdown
      const dropdown = document.getElementById("search-dropdown");
      if (dropdown?.contains(target)) return;
      setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  // ⌘K shortcut
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        inputRef.current?.focus();
        setOpen(true);
      }
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, []);

  const handleSelect = useCallback(
    (sessionId: string) => {
      setOpen(false);
      setQuery("");
      navigate({ to: "/sessions/$sessionId", params: { sessionId } });
    },
    [navigate],
  );

  const showDropdown = open && debouncedQuery.length >= 2;
  const hasResults = data && data.items.length > 0;
  const noResults = data && data.items.length === 0 && !isFetching;

  return (
    <header className="flex h-10 shrink-0 items-center justify-between gap-4 border-b border-outline-variant bg-surface/80 px-4 backdrop-blur-md">
      <div className="flex flex-1 items-center gap-4">
        {/* Search */}
        <div ref={wrapperRef} className="relative">
          <div className="flex items-center gap-2 rounded border border-outline-variant/30 bg-surface-container-low px-2 py-1 transition-colors focus-within:border-primary/50">
            <Search size={14} className="text-outline" />
            <input
              ref={inputRef}
              type="text"
              placeholder="⌘K 검색..."
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setOpen(true);
              }}
              onFocus={() => setOpen(true)}
              onKeyDown={(e) => {
                if (e.key === "Escape") {
                  setOpen(false);
                  inputRef.current?.blur();
                }
              }}
              className="w-48 border-none bg-transparent font-mono text-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-0"
            />
          </div>
        </div>
        {children}
      </div>
      <div className="flex items-center gap-3">
        <button
          onClick={toggleTheme}
          className="text-on-surface/40 transition-colors hover:text-on-surface"
          title={theme === "dark" ? "라이트 모드" : "다크 모드"}
        >
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>

      {/* Dropdown — portal to body so it escapes header's backdrop-blur/opacity */}
      {showDropdown &&
        createPortal(
          <div
            id="search-dropdown"
            className="fixed z-[9999] w-96 overflow-hidden rounded border border-outline-variant/30 bg-surface-container shadow-lg"
            style={{
              top: dropdownPos.top,
              left: dropdownPos.left,
            }}
            onMouseDown={(e) => e.preventDefault()}
          >
            {hasResults ? (
              <ul className="max-h-80 overflow-y-auto py-1">
                {data.items.map((s) => (
                  <li key={s.session_id}>
                    <button
                      type="button"
                      onClick={() => handleSelect(s.session_id)}
                      className="flex w-full flex-col gap-0.5 px-3 py-2 text-left transition-colors hover:bg-white/5"
                    >
                      <span className="truncate text-sm text-on-surface">
                        {s.summary || s.session_id.slice(0, 8)}
                      </span>
                      <span className="flex items-center gap-2 text-xs text-on-surface-variant/70">
                        <span>{baseName(s.decoded_cwd)}</span>
                        <span>·</span>
                        <span>{timeAgo(s.last_message_at)}</span>
                        <span>·</span>
                        <span>{s.message_count}건</span>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            ) : noResults ? (
              <div className="px-3 py-4 text-center text-sm text-on-surface-variant/50">
                검색 결과 없음
              </div>
            ) : (
              <div className="px-3 py-3 text-center text-xs text-on-surface-variant/40">
                검색 중...
              </div>
            )}
          </div>,
          document.body,
        )}
    </header>
  );
}
