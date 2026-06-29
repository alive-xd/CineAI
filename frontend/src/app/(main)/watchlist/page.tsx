"use client";
// src/app/(main)/watchlist/page.tsx
import Image from "next/image";
import Link from "next/link";
import { Bookmark, CheckCircle2, Circle, Trash2, Star } from "lucide-react";
import Navbar from "@/components/layout/Navbar";
import { useWatchlist } from "@/hooks";
import { useAuthStore } from "@/store/authStore";
import { cn, formatRuntime } from "@/lib/utils";
import type { WatchlistItem } from "@/types";

export default function WatchlistPage() {
  const { isAuthenticated } = useAuthStore();
  const { watchlist, isLoading, markWatched, remove } = useWatchlist();

  const toWatch = watchlist.filter(w => !w.watched);
  const watched  = watchlist.filter(w =>  w.watched);

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--surface)" }}>
        <div className="text-center">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
            style={{ background: "rgba(229,9,20,0.1)" }}>
            <Bookmark className="w-8 h-8 text-brand" />
          </div>
          <h2 className="text-xl font-bold mb-2">Sign in to see your watchlist</h2>
          <p className="text-zinc-500 text-sm mb-6">Save movies you want to watch later</p>
          <Link href="/login" className="btn-primary">Sign in</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: "var(--surface)" }}>
      <Navbar />
      <main className="pt-24 pb-20 px-5 md:px-8 lg:px-12 max-w-screen-lg mx-auto">

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-black tracking-tight mb-1">Watchlist</h1>
          <p className="text-zinc-500 text-sm">
            {toWatch.length} to watch · {watched.length} watched
          </p>
        </div>

        {/* Loading */}
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-24 skeleton rounded-2xl" />
            ))}
          </div>
        ) : watchlist.length === 0 ? (
          <div className="text-center py-24 rounded-3xl border border-white/5"
            style={{ background: "var(--surface-card)" }}>
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
              style={{ background: "rgba(229,9,20,0.08)" }}>
              <Bookmark className="w-7 h-7 text-brand opacity-40" />
            </div>
            <h3 className="text-lg font-bold mb-2">Nothing saved yet</h3>
            <p className="text-zinc-500 text-sm mb-6">Save movies from any page to watch later</p>
            <Link href="/movies" className="btn-primary">Browse movies</Link>
          </div>
        ) : (
          <div className="space-y-10">

            {/* To watch */}
            {toWatch.length > 0 && (
              <div>
                <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest mb-4">
                  Up next — {toWatch.length}
                </p>
                <div className="space-y-2">
                  {toWatch.map(item => (
                    <WatchlistRow
                      key={item.id}
                      item={item}
                      onMarkWatched={() => markWatched(item.movie.tmdb_id, true)}
                      onRemove={() => remove(item.movie.tmdb_id)}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Watched */}
            {watched.length > 0 && (
              <div>
                <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest mb-4">
                  Watched — {watched.length}
                </p>
                <div className="space-y-2 opacity-50">
                  {watched.map(item => (
                    <WatchlistRow
                      key={item.id}
                      item={item}
                      onMarkWatched={() => markWatched(item.movie.tmdb_id, false)}
                      onRemove={() => remove(item.movie.tmdb_id)}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

function WatchlistRow({ item, onMarkWatched, onRemove }: {
  item: WatchlistItem;
  onMarkWatched: () => void;
  onRemove: () => void;
}) {
  const { movie, watched } = item;
  return (
    <div className={cn(
      "flex items-center gap-4 rounded-2xl p-3.5 border transition-all duration-200",
      "hover:border-white/10"
    )}
    style={{ background: "var(--surface-card)", borderColor: "rgba(255,255,255,0.05)" }}>

      {/* Poster */}
      <Link href={`/movies/${movie.tmdb_id}`} className="shrink-0">
        <div className="w-12 h-[72px] rounded-xl overflow-hidden relative border border-white/5"
          style={{ background: "var(--surface-raised)" }}>
          {movie.poster_url ? (
            <Image src={movie.poster_url} alt={movie.title} fill sizes="48px" className="object-cover" />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center text-lg opacity-30">🎬</div>
          )}
        </div>
      </Link>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <Link href={`/movies/${movie.tmdb_id}`}>
          <h3 className="text-sm font-semibold text-white hover:text-zinc-300 transition-colors line-clamp-1">
            {movie.title}
          </h3>
        </Link>
        <div className="flex items-center gap-2 mt-1">
          {movie.year && <span className="text-xs text-zinc-600">{movie.year}</span>}
          {movie.runtime && <span className="text-xs text-zinc-600">{formatRuntime(movie.runtime)}</span>}
          <span className="flex items-center gap-1">
            <Star className="w-2.5 h-2.5 fill-yellow-400 text-yellow-400" />
            <span className="text-xs text-zinc-500">{movie.vote_average.toFixed(1)}</span>
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1.5 shrink-0">
        <button
          onClick={onMarkWatched}
          className="w-8 h-8 rounded-xl flex items-center justify-center transition-all duration-200 border"
          style={{
            background: watched ? "rgba(34,197,94,0.1)" : "rgba(255,255,255,0.04)",
            borderColor: watched ? "rgba(34,197,94,0.25)" : "rgba(255,255,255,0.06)",
          }}
          title={watched ? "Mark unwatched" : "Mark watched"}
        >
          {watched
            ? <CheckCircle2 className="w-4 h-4 text-green-400" />
            : <Circle className="w-4 h-4 text-zinc-600" />
          }
        </button>
        <button
          onClick={onRemove}
          className="w-8 h-8 rounded-xl flex items-center justify-center transition-all duration-200 border border-white/5 hover:border-red-500/25 hover:bg-red-500/10"
          style={{ background: "rgba(255,255,255,0.04)" }}
        >
          <Trash2 className="w-3.5 h-3.5 text-zinc-600 hover:text-red-400 transition-colors" />
        </button>
      </div>
    </div>
  );
}
