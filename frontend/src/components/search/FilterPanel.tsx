"use client";
// src/components/search/FilterPanel.tsx
import { useState } from "react";
import { Filter, ChevronDown } from "lucide-react";
import { cn, GENRES, LANGUAGES, genreColour } from "@/lib/utils";
import type { SearchFilters } from "@/types";

interface Props {
  filters: SearchFilters;
  onChange: (f: SearchFilters) => void;
}

export default function FilterPanel({ filters, onChange }: Props) {
  const [open, setOpen] = useState(false);

  const activeCount =
    (filters.genres?.length ?? 0) +
    (filters.year_min || filters.year_max ? 1 : 0) +
    (filters.rating_min ? 1 : 0) +
    (filters.language   ? 1 : 0);

  const hasFilters = activeCount > 0;

  const toggleGenre = (g: string) => {
    const current = filters.genres ?? [];
    const next = current.includes(g)
      ? current.filter(x => x !== g)
      : [...current, g];
    onChange({ ...filters, genres: next.length ? next : undefined });
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(v => !v)}
        className={cn(
          "flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 border"
        )}
        style={open || hasFilters
          ? { background: "var(--brand)", borderColor: "transparent", color: "white" }
          : { background: "rgba(255,255,255,0.04)", borderColor: "rgba(255,255,255,0.07)", color: "rgba(255,255,255,0.5)" }
        }
      >
        <Filter className="w-3.5 h-3.5" />
        Filters
        {hasFilters && (
          <span className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold"
            style={{ background: "rgba(255,255,255,0.2)" }}>
            {activeCount}
          </span>
        )}
        <ChevronDown className={cn("w-3.5 h-3.5 transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <div className="absolute left-0 top-full mt-2 z-40 w-80 rounded-2xl p-5 shadow-2xl shadow-black/60 animate-scale-in"
          style={{ background: "var(--surface-card)", border: "1px solid rgba(255,255,255,0.08)" }}>

          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-white">Filters</h3>
            {hasFilters && (
              <button
                onClick={() => onChange({})}
                className="text-xs text-brand hover:underline font-medium"
              >
                Clear all
              </button>
            )}
          </div>

          {/* Genres */}
          <div className="mb-5">
            <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest mb-2.5">Genre</p>
            <div className="flex flex-wrap gap-1.5">
              {GENRES.map(g => {
                const active = (filters.genres ?? []).includes(g);
                return (
                  <button
                    key={g}
                    onClick={() => toggleGenre(g)}
                    className={cn("tag text-[10px] transition-all duration-150", active ? genreColour(g) : "")}
                    style={!active ? {
                      background: "rgba(255,255,255,0.05)",
                      color: "rgba(255,255,255,0.4)",
                      border: "1px solid rgba(255,255,255,0.07)",
                    } : {}}
                  >
                    {g}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Year */}
          <div className="mb-5">
            <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest mb-2.5">Year</p>
            <div className="flex items-center gap-2">
              <input
                type="number" min={1900} max={2026} placeholder="From"
                value={filters.year_min ?? ""}
                onChange={e => onChange({ ...filters, year_min: e.target.value ? +e.target.value : undefined })}
                className="input-base py-2 text-sm w-28"
              />
              <span className="text-zinc-700 text-sm">—</span>
              <input
                type="number" min={1900} max={2026} placeholder="To"
                value={filters.year_max ?? ""}
                onChange={e => onChange({ ...filters, year_max: e.target.value ? +e.target.value : undefined })}
                className="input-base py-2 text-sm w-28"
              />
            </div>
          </div>

          {/* Rating */}
          <div className="mb-5">
            <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest mb-2.5">
              Min Rating — {filters.rating_min ? `${filters.rating_min}+` : "Any"}
            </p>
            <input
              type="range" min={0} max={9} step={0.5}
              value={filters.rating_min ?? 0}
              onChange={e => onChange({ ...filters, rating_min: +e.target.value || undefined })}
              className="w-full accent-red-600"
            />
          </div>

          {/* Language */}
          <div>
            <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest mb-2.5">Language</p>
            <select
              value={filters.language ?? ""}
              onChange={e => onChange({ ...filters, language: e.target.value || undefined })}
              className="input-base py-2 text-sm"
            >
              <option value="">Any language</option>
              {LANGUAGES.map(l => (
                <option key={l.code} value={l.code}>{l.label}</option>
              ))}
            </select>
          </div>
        </div>
      )}
    </div>
  );
}
