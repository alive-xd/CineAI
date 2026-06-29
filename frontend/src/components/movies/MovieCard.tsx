"use client";
// src/components/movies/MovieCard.tsx
import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import { Bookmark, BookmarkCheck, Star, Play } from "lucide-react";
import { cn, formatRuntime, genreColour, truncate } from "@/lib/utils";
import type { MovieCard as MovieCardType } from "@/types";
import { useWatchlist } from "@/hooks";
import { useAuthStore } from "@/store/authStore";
import StarRating from "./StarRating";

interface Props {
  movie: MovieCardType;
  showRating?: boolean;
  className?: string;
  priority?: boolean;
}

export default function MovieCard({ movie, showRating = false, className, priority = false }: Props) {
  const [hovered,  setHovered]  = useState(false);
  const [imgError, setImgError] = useState(false);
  const { isAuthenticated }     = useAuthStore();
  const { watchlistIds, toggle } = useWatchlist();
  const inWatchlist = watchlistIds.has(movie.tmdb_id);

  const handleWatchlist = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isAuthenticated) return;
    await toggle(movie.tmdb_id);
  };

  return (
    <Link href={`/movies/${movie.tmdb_id}`}>
      <div
        className={cn(
          "relative group rounded-2xl overflow-hidden cursor-pointer",
          "border border-white/5 hover:border-white/12",
          "transition-all duration-400 ease-out",
          "hover:-translate-y-1.5 hover:shadow-2xl hover:shadow-black/60",
          className
        )}
        style={{ background: "var(--surface-card)" }}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      >
        {/* Poster */}
        <div className="aspect-[2/3] relative overflow-hidden bg-zinc-900">
          {movie.poster_url && !imgError ? (
            <Image
              src={movie.poster_url}
              alt={movie.title}
              fill
              sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 20vw"
              className={cn(
                "object-cover transition-transform duration-500",
                hovered && "scale-105"
              )}
              onError={() => setImgError(true)}
              priority={priority}
            />
          ) : (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-zinc-900 gap-3">
              <span className="text-4xl opacity-40">🎬</span>
              <p className="text-xs text-zinc-600 font-medium text-center px-3 leading-tight">
                {truncate(movie.title, 30)}
              </p>
            </div>
          )}

          {/* Cinematic gradient overlay — always visible at bottom */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />

          {/* Hover overlay */}
          <div className={cn(
            "absolute inset-0 bg-black/40 transition-opacity duration-300",
            hovered ? "opacity-100" : "opacity-0"
          )} />

          {/* Rating badge — top left */}
          <div className="absolute top-2.5 left-2.5 flex items-center gap-1 bg-black/75 backdrop-blur-md rounded-full px-2 py-1 border border-white/10">
            <Star className="w-2.5 h-2.5 fill-yellow-400 text-yellow-400" />
            <span className="text-[11px] font-bold text-white leading-none">
              {movie.vote_average.toFixed(1)}
            </span>
          </div>

          {/* Watchlist button — top right */}
          {isAuthenticated && (
            <button
              onClick={handleWatchlist}
              className={cn(
                "absolute top-2.5 right-2.5 w-8 h-8 rounded-xl backdrop-blur-md",
                "flex items-center justify-center transition-all duration-200",
                "border border-white/10",
                inWatchlist
                  ? "bg-brand text-white border-brand/50"
                  : cn(
                      "bg-black/70 text-white",
                      hovered ? "opacity-100" : "opacity-0"
                    )
              )}
            >
              {inWatchlist
                ? <BookmarkCheck className="w-3.5 h-3.5" />
                : <Bookmark className="w-3.5 h-3.5" />
              }
            </button>
          )}

          {/* Play button — center on hover */}
          <div className={cn(
            "absolute inset-0 flex items-center justify-center transition-all duration-300",
            hovered ? "opacity-100 scale-100" : "opacity-0 scale-90"
          )}>
            <div className="w-12 h-12 rounded-full bg-white/15 backdrop-blur-md border border-white/25 flex items-center justify-center">
              <Play className="w-5 h-5 fill-white text-white ml-0.5" />
            </div>
          </div>

          {/* Year + runtime at bottom of poster */}
          <div className={cn(
            "absolute bottom-2.5 left-2.5 right-2.5 flex items-center justify-between",
            "transition-all duration-300",
            hovered ? "opacity-100 translate-y-0" : "opacity-0 translate-y-1"
          )}>
            <span className="text-[11px] text-white/70 font-medium">{movie.year}</span>
            {movie.runtime && (
              <span className="text-[11px] text-white/70 font-medium">{formatRuntime(movie.runtime)}</span>
            )}
          </div>
        </div>

        {/* Card body */}
        <div className="p-3">
          <h3 className="font-semibold text-[13px] leading-tight line-clamp-1 text-white mb-1.5">
            {movie.title}
          </h3>

          {/* Genre tags */}
          {movie.genres.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {movie.genres.slice(0, 2).map(g => (
                <span
                  key={g}
                  className={cn("tag", genreColour(g))}
                  style={{ fontSize: "9px" }}
                >
                  {g}
                </span>
              ))}
            </div>
          )}

          {showRating && (
            <div className="mt-2.5 pt-2 border-t border-white/5">
              <StarRating movieId={movie.tmdb_id} />
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}
