"use client";
// src/app/(main)/movies/page.tsx
import { useState } from "react";
import Navbar from "@/components/layout/Navbar";
import MovieGrid from "@/components/movies/MovieGrid";
import FilterPanel from "@/components/search/FilterPanel";
import { usePopular, useTopRated, useTrending } from "@/hooks";
import { cn } from "@/lib/utils";
import type { SearchFilters } from "@/types";

const TABS = [
  { key: "trending", label: "Trending"  },
  { key: "popular",  label: "Popular"   },
  { key: "top",      label: "Top Rated" },
] as const;

type Tab = (typeof TABS)[number]["key"];

export default function MoviesPage() {
  const [tab,     setTab]     = useState<Tab>("trending");
  const [filters, setFilters] = useState<SearchFilters>({});

  const { data: trending, isLoading: tl } = useTrending();
  const { data: popular,  isLoading: pl } = usePopular();
  const { data: topRated, isLoading: rl } = useTopRated();

  const moviesByTab   = { trending: trending ?? [], popular: popular ?? [], top: topRated ?? [] };
  const loadingByTab  = { trending: tl, popular: pl, top: rl };

  const filtered = moviesByTab[tab].filter(m => {
    if (filters.genres?.length && !filters.genres.some(g => m.genres.includes(g))) return false;
    if (filters.year_min   && m.year          && m.year < filters.year_min)           return false;
    if (filters.year_max   && m.year          && m.year > filters.year_max)           return false;
    if (filters.rating_min && m.vote_average  < filters.rating_min)                   return false;
    return true;
  });

  return (
    <div className="min-h-screen" style={{ background: "var(--surface)" }}>
      <Navbar />
      <main className="pt-24 pb-20 px-5 md:px-8 lg:px-12 max-w-screen-2xl mx-auto">

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-black tracking-tight mb-1">Movies</h1>
          <p className="text-zinc-500 text-sm">Browse trending, popular, and critically acclaimed films</p>
        </div>

        {/* Tabs + filters */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <div className="flex gap-1 p-1 rounded-xl" style={{ background: "var(--surface-raised)" }}>
            {TABS.map(t => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={cn(
                  "px-5 py-2 rounded-lg text-sm font-semibold transition-all duration-200",
                  tab === t.key
                    ? "text-white shadow-lg"
                    : "text-zinc-500 hover:text-white"
                )}
                style={tab === t.key ? { background: "var(--brand)" } : {}}
              >
                {t.label}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-3">
            <FilterPanel filters={filters} onChange={setFilters} />
            {!loadingByTab[tab] && (
              <span className="text-xs text-zinc-600">
                {filtered.length} film{filtered.length !== 1 ? "s" : ""}
              </span>
            )}
          </div>
        </div>

        <MovieGrid
          movies={filtered}
          isLoading={loadingByTab[tab]}
          showRating
          emptySlot={
            <div className="text-center py-16 col-span-full">
              <p className="text-zinc-500 font-medium mb-2">No movies match your filters</p>
              <button onClick={() => setFilters({})} className="text-brand text-sm hover:underline">
                Clear filters
              </button>
            </div>
          }
        />
      </main>
    </div>
  );
}
