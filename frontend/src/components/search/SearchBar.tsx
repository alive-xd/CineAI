"use client";
// src/components/search/SearchBar.tsx
import { useState, useRef, useEffect } from "react";
import { Search, Sparkles, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  onSearch: (query: string, mode: "keyword" | "semantic") => void;
  isLoading?: boolean;
  defaultQuery?: string;
  placeholder?: string;
  autoFocus?: boolean;
}

const SEMANTIC_HINTS = [
  "mind bending sci-fi movies",
  "dark emotional thrillers",
  "movies like Interstellar but sadder",
  "feel-good heist comedies",
  "philosophical slow-burn dramas",
  "movies about loneliness and connection",
];

export default function SearchBar({
  onSearch, isLoading = false, defaultQuery = "", placeholder, autoFocus = false,
}: Props) {
  const [query, setQuery] = useState(defaultQuery);
  const [mode,  setMode]  = useState<"keyword" | "semantic">("keyword");
  const [hint,  setHint]  = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (mode !== "semantic") return;
    const id = setInterval(() => setHint(h => (h + 1) % SEMANTIC_HINTS.length), 3000);
    return () => clearInterval(id);
  }, [mode]);

  useEffect(() => {
    if (autoFocus) inputRef.current?.focus();
  }, [autoFocus]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    onSearch(query.trim(), mode);
  };

  return (
    <form onSubmit={handleSubmit} className="w-full space-y-3">

      {/* Mode toggle */}
      <div className="flex gap-2">
        {(["keyword", "semantic"] as const).map(m => (
          <button
            key={m}
            type="button"
            onClick={() => setMode(m)}
            className={cn(
              "flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 border",
              mode === m
                ? "text-white"
                : "text-zinc-500 hover:text-zinc-300"
            )}
            style={mode === m
              ? { background: "var(--brand)", borderColor: "transparent" }
              : { background: "rgba(255,255,255,0.04)", borderColor: "rgba(255,255,255,0.07)" }
            }
          >
            {m === "semantic" && <Sparkles className="w-3.5 h-3.5" />}
            {m === "keyword" ? "Keyword" : "AI Semantic"}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-600 pointer-events-none" />

        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder={placeholder ?? (mode === "semantic" ? SEMANTIC_HINTS[hint] : "Search movies, directors, actors…")}
          className="input-base pl-12 pr-28 py-4 text-base rounded-2xl"
        />

        <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
          {query && (
            <button
              type="button"
              onClick={() => { setQuery(""); inputRef.current?.focus(); }}
              className="w-7 h-7 rounded-lg flex items-center justify-center text-zinc-600 hover:text-zinc-300 transition-colors"
              style={{ background: "rgba(255,255,255,0.05)" }}
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
          <button
            type="submit"
            disabled={!query.trim() || isLoading}
            className="px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
            style={{ background: "var(--brand)", color: "white" }}
          >
            {isLoading ? "…" : "Search"}
          </button>
        </div>
      </div>

      {/* Semantic hint */}
      {mode === "semantic" && (
        <p className="flex items-center gap-1.5 text-xs text-zinc-600">
          <Sparkles className="w-3 h-3 text-brand" />
          AI understands concepts, emotions, and descriptions — try natural language
        </p>
      )}
    </form>
  );
}
