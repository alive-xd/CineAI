"use client";
// src/app/(main)/search/page.tsx
import { useState } from "react";
import { Sparkles, Search as SearchIcon, Zap, Loader2 } from "lucide-react";
import Navbar from "@/components/layout/Navbar";
import SearchBar from "@/components/search/SearchBar";
import FilterPanel from "@/components/search/FilterPanel";
import MovieGrid from "@/components/movies/MovieGrid";
import { useSearch } from "@/hooks";
import type { SearchFilters } from "@/types";

const MOOD_PROMPTS = [
  "movies about loneliness",
  "something like Interstellar",
  "mind-bending thriller",
  "emotional sci-fi",
  "dark psychological drama",
  "feel-good rainy day movie",
];

export default function SearchPage() {
  const [filters, setFilters] = useState<SearchFilters>({});
  const { results, isLoading, isLoadingMore, error, lastQuery, mode, search, loadMore, clear } = useSearch();

  const handleSearch = (query: string, searchMode: "keyword" | "semantic") => {
    search(query, searchMode, filters);
  };

  const handleMoodPrompt = (prompt: string) => {
    search(prompt, "semantic", filters);
  };

  return (
    <div className="min-h-screen" style={{ background: "var(--surface)" }}>
      <Navbar />

      <main className="pt-24 pb-20 px-5 md:px-8 lg:px-12 max-w-screen-2xl mx-auto">

        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-6 h-6 rounded-lg flex items-center justify-center"
              style={{ background: "rgba(229,9,20,0.12)" }}>
              <Sparkles className="w-3.5 h-3.5 text-brand" />
            </div>
            <h1 className="text-3xl font-black tracking-tight">Discover</h1>
          </div>
          <p className="text-zinc-500 text-sm ml-8">
            Keyword search or describe what you're in the mood for using AI
          </p>
        </div>

        {/* Search */}
        <div className="mb-5 space-y-4">
          <SearchBar onSearch={handleSearch} isLoading={isLoading} autoFocus />
          <div className="flex items-center gap-3 flex-wrap">
            <FilterPanel filters={filters} onChange={setFilters} />
            {lastQuery && (
              <button
                onClick={clear}
                className="text-xs text-zinc-500 hover:text-white transition-colors"
              >
                Clear results
              </button>
            )}
          </div>
        </div>

        {/* Mood prompts */}
        {!lastQuery && !isLoading && (
          <div className="mb-12">
            <div className="flex items-center gap-2 mb-4">
              <Zap className="w-3.5 h-3.5 text-brand" />
              <p className="text-xs text-zinc-500 font-medium uppercase tracking-widest">
                Try AI Semantic Search
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {MOOD_PROMPTS.map(prompt => (
                <button
                  key={prompt}
                  onClick={() => handleMoodPrompt(prompt)}
                  className="text-xs px-4 py-2 rounded-full transition-all duration-200 hover:text-white"
                  style={{
                    background: "rgba(255,255,255,0.05)",
                    border: "1px solid rgba(255,255,255,0.08)",
                    color: "rgba(255,255,255,0.5)",
                  }}
                  onMouseEnter={e => {
                    (e.currentTarget as HTMLElement).style.background = "rgba(229,9,20,0.1)";
                    (e.currentTarget as HTMLElement).style.borderColor = "rgba(229,9,20,0.25)";
                    (e.currentTarget as HTMLElement).style.color = "#E50914";
                  }}
                  onMouseLeave={e => {
                    (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)";
                    (e.currentTarget as HTMLElement).style.borderColor = "rgba(255,255,255,0.08)";
                    (e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.5)";
                  }}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="text-center py-8 text-red-400 text-sm">{error}</div>
        )}

        {/* Result count */}
        {lastQuery && !isLoading && (
          <div className="flex items-center gap-2 mb-6">
            {mode === "semantic" && <Sparkles className="w-3.5 h-3.5 text-brand" />}
            <span className="text-sm text-zinc-500">
              <span className="text-white font-semibold">{results.length}</span> result{results.length !== 1 ? "s" : ""} for{" "}
              <span className="text-zinc-300">"{lastQuery}"</span>
              {mode === "semantic" && (
                <span className="ml-2 text-xs px-2 py-0.5 rounded-full"
                  style={{ background: "rgba(229,9,20,0.1)", color: "#E50914" }}>
                  AI Semantic
                </span>
              )}
            </span>
          </div>
        )}

        {/* Empty state */}
        {!lastQuery && !isLoading && (
          <div className="text-center py-20 text-zinc-600">
            <SearchIcon className="w-10 h-10 mx-auto mb-4 opacity-20" />
            <p className="text-base font-medium text-zinc-500 mb-1">What are you in the mood for?</p>
            <p className="text-sm">Type a query above or click a prompt to search with AI</p>
          </div>
        )}

        {/* Results */}
        <MovieGrid
          movies={results}
          isLoading={isLoading}
          skeletonCount={12}
          showRating
          emptySlot={
            lastQuery ? (
              <div className="text-center py-16 text-zinc-600 col-span-full">
                <p className="text-base font-medium text-zinc-500 mb-1">No results found</p>
                <p className="text-sm">Try switching to AI Semantic search for natural language queries</p>
              </div>
            ) : undefined
          }
        />

        {/* Load More — only for semantic search with results */}
        {lastQuery && mode === "semantic" && results.length > 0 && !isLoading && (
          <div className="flex justify-center mt-10">
            <button
              onClick={loadMore}
              disabled={isLoadingMore}
              className="flex items-center gap-2 px-6 py-2.5 rounded-full text-sm font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                background: "rgba(255,255,255,0.05)",
                border: "1px solid rgba(255,255,255,0.1)",
                color: "rgba(255,255,255,0.7)",
              }}
              onMouseEnter={e => {
                if (!isLoadingMore) {
                  (e.currentTarget as HTMLElement).style.background = "rgba(229,9,20,0.1)";
                  (e.currentTarget as HTMLElement).style.borderColor = "rgba(229,9,20,0.25)";
                  (e.currentTarget as HTMLElement).style.color = "#E50914";
                }
              }}
              onMouseLeave={e => {
                (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.05)";
                (e.currentTarget as HTMLElement).style.borderColor = "rgba(255,255,255,0.1)";
                (e.currentTarget as HTMLElement).style.color = "rgba(255,255,255,0.7)";
              }}
            >
              {isLoadingMore ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Loading more...
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  Load more results
                </>
              )}
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
