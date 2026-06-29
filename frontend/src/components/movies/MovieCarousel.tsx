"use client";
// src/components/movies/MovieCarousel.tsx
import { useRef, useState, useCallback } from "react";
import { ChevronLeft, ChevronRight, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import MovieCard from "./MovieCard";
import MovieCardSkeleton from "./MovieCardSkeleton";
import type { MovieCard as MovieCardType } from "@/types";

interface Props {
  title: string;
  subtitle?: string;
  movies: MovieCardType[];
  isLoading?: boolean;
  showRating?: boolean;
  emptyMessage?: string;
  viewAllHref?: string;
}

export default function MovieCarousel({
  title, subtitle, movies, isLoading = false,
  showRating = false, emptyMessage, viewAllHref,
}: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [canScrollLeft,  setCanScrollLeft]  = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);

  const updateScrollState = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    setCanScrollLeft(el.scrollLeft > 4);
    setCanScrollRight(el.scrollLeft + el.clientWidth < el.scrollWidth - 4);
  }, []);

  const scroll = (dir: "left" | "right") => {
    const el = scrollRef.current;
    if (!el) return;
    const cardWidth = el.querySelector("div")?.offsetWidth ?? 180;
    el.scrollBy({ left: dir === "left" ? -(cardWidth * 3) : cardWidth * 3, behavior: "smooth" });
  };

  return (
    <section>
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">{title}</h2>
          {subtitle && (
            <p className="text-sm text-zinc-500 mt-0.5">{subtitle}</p>
          )}
        </div>

        <div className="flex items-center gap-2">
          {viewAllHref && (
            <a
              href={viewAllHref}
              className="hidden sm:flex items-center gap-1 text-xs text-zinc-500 hover:text-white transition-colors mr-2"
            >
              See all <ArrowRight className="w-3 h-3" />
            </a>
          )}
          <button
            onClick={() => scroll("left")}
            disabled={!canScrollLeft}
            className={cn(
              "w-8 h-8 rounded-xl border flex items-center justify-center transition-all duration-200",
              canScrollLeft
                ? "border-white/10 bg-white/5 text-white hover:bg-white/10"
                : "border-white/4 bg-transparent text-zinc-700 cursor-not-allowed"
            )}
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => scroll("right")}
            disabled={!canScrollRight}
            className={cn(
              "w-8 h-8 rounded-xl border flex items-center justify-center transition-all duration-200",
              canScrollRight
                ? "border-white/10 bg-white/5 text-white hover:bg-white/10"
                : "border-white/4 bg-transparent text-zinc-700 cursor-not-allowed"
            )}
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Scroll track */}
      <div
        ref={scrollRef}
        onScroll={updateScrollState}
        className="flex gap-3 overflow-x-auto scrollbar-hide pb-1"
      >
        {isLoading
          ? Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="shrink-0 w-36 sm:w-40 md:w-44">
                <MovieCardSkeleton />
              </div>
            ))
          : movies.length > 0
            ? movies.map((movie, i) => (
                <div key={movie.tmdb_id} className="shrink-0 w-36 sm:w-40 md:w-44">
                  <MovieCard movie={movie} showRating={showRating} priority={i < 5} />
                </div>
              ))
            : emptyMessage && (
                <p className="text-zinc-500 text-sm py-8 px-1">{emptyMessage}</p>
              )
        }
      </div>
    </section>
  );
}
