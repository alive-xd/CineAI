"use client";
// src/app/movies/[id]/page.tsx
import Image from "next/image";
import Link from "next/link";
import { Star, Clock, Globe, Bookmark, BookmarkCheck, ArrowLeft, Sparkles, Tag } from "lucide-react";
import Navbar from "@/components/layout/Navbar";
import MovieCarousel from "@/components/movies/MovieCarousel";
import StarRating from "@/components/movies/StarRating";
import { useMovieDetail, useSimilarMovies, useWatchlist } from "@/hooks";
import { useAuthStore } from "@/store/authStore";
import { cn, formatRuntime, genreColour } from "@/lib/utils";

interface Props {
  params: { id: string };
}

export default function MovieDetailPage({ params }: Props) {
  const movieId = Number(params.id);
  const { data: movie, isLoading } = useMovieDetail(movieId);
  const { data: similar, isLoading: similarLoading } = useSimilarMovies(movieId);
  const { isAuthenticated } = useAuthStore();
  const { watchlistIds, toggle } = useWatchlist();
  const inWatchlist = watchlistIds.has(movieId);

  if (isLoading) return <MovieDetailSkeleton />;
  if (!movie) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--surface)" }}>
        <div className="text-center">
          <p className="text-zinc-500 text-lg">Movie not found</p>
          <Link href="/" className="btn-ghost mt-4 inline-flex">Go home</Link>
        </div>
      </div>
    );
  }

  const similarCards = similar?.map(s => s.movie) ?? [];

  return (
    <div className="min-h-screen" style={{ background: "var(--surface)" }}>
      <Navbar />

      {/* ── Cinematic Backdrop ──────────────────────────────────── */}
      <div className="relative h-[65vh] min-h-[480px] overflow-hidden">
        {movie.backdrop_url ? (
          <Image
            src={movie.backdrop_url}
            alt={movie.title}
            fill priority
            className="object-cover"
            sizes="100vw"
          />
        ) : (
          <div className="absolute inset-0 bg-gradient-to-br from-zinc-900 to-black" />
        )}

        {/* Layered overlays */}
        <div className="absolute inset-0 overlay-left" />
        <div className="absolute inset-0 overlay-bottom" />
        <div className="absolute inset-0 overlay-vignette" />

        {/* Back */}
        <Link
          href="javascript:history.back()"
          className="absolute top-20 left-5 md:left-8 lg:left-12 flex items-center gap-2 text-sm text-zinc-400 hover:text-white transition-colors z-10"
        >
          <div className="w-8 h-8 rounded-xl flex items-center justify-center glass">
            <ArrowLeft className="w-4 h-4" />
          </div>
        </Link>
      </div>

      {/* ── Main content ────────────────────────────────────────── */}
      <div className="relative z-10 -mt-48 px-5 md:px-8 lg:px-12 pb-20 max-w-screen-xl mx-auto">
        <div className="flex flex-col md:flex-row gap-8 md:gap-10">

          {/* Poster */}
          <div className="shrink-0 w-44 md:w-52 mx-auto md:mx-0">
            <div
              className="rounded-2xl overflow-hidden shadow-2xl shadow-black/60 aspect-[2/3] relative border border-white/8"
              style={{ background: "var(--surface-raised)" }}
            >
              {movie.poster_url ? (
                <Image src={movie.poster_url} alt={movie.title} fill sizes="208px" className="object-cover" />
              ) : (
                <div className="absolute inset-0 flex items-center justify-center text-5xl opacity-30">🎬</div>
              )}
            </div>
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0 pt-2 md:pt-32">

            {/* Title */}
            <h1 className="text-3xl md:text-5xl font-black tracking-tight leading-none mb-2 text-white">
              {movie.title}
            </h1>
            {movie.tagline && (
              <p className="text-zinc-500 italic text-sm md:text-base mb-5">{movie.tagline}</p>
            )}

            {/* Meta */}
            <div className="flex flex-wrap items-center gap-3 mb-5">
              {movie.year && (
                <span className="text-sm text-zinc-400 font-medium">{movie.year}</span>
              )}
              {movie.runtime && (
                <span className="flex items-center gap-1.5 text-sm text-zinc-400">
                  <Clock className="w-3.5 h-3.5" />{formatRuntime(movie.runtime)}
                </span>
              )}
              {movie.original_language && (
                <span className="flex items-center gap-1.5 text-sm text-zinc-400">
                  <Globe className="w-3.5 h-3.5" />{movie.original_language.toUpperCase()}
                </span>
              )}
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-full font-semibold text-sm"
                style={{ background: "rgba(245,197,24,0.12)", color: "#F5C518" }}>
                <Star className="w-3.5 h-3.5 fill-yellow-400" />
                {movie.vote_average.toFixed(1)}
                <span className="text-xs font-normal opacity-60">
                  ({movie.vote_count?.toLocaleString()})
                </span>
              </div>
            </div>

            {/* Genres */}
            {movie.genres.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-4">
                {movie.genres.map(g => (
                  <span key={g} className={cn("tag", genreColour(g))}>{g}</span>
                ))}
              </div>
            )}

            {/* Mood tags */}
            {movie.mood_tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-5">
                {movie.mood_tags.map(t => (
                  <span key={t} className="tag text-[10px]"
                    style={{ background: "rgba(229,9,20,0.08)", color: "rgba(255,255,255,0.5)", border: "1px solid rgba(229,9,20,0.15)" }}>
                    {t}
                  </span>
                ))}
              </div>
            )}

            {/* Overview */}
            {movie.overview && (
              <p className="text-zinc-400 leading-relaxed mb-6 max-w-2xl text-sm md:text-base">
                {movie.overview}
              </p>
            )}

            {/* Director + Cast */}
            <div className="flex flex-wrap gap-6 mb-7">
              {movie.director && (
                <div>
                  <p className="text-[10px] text-zinc-600 uppercase tracking-widest mb-1 font-medium">Director</p>
                  <p className="text-sm font-semibold text-white">{movie.director}</p>
                </div>
              )}
              {movie.top_cast.length > 0 && (
                <div>
                  <p className="text-[10px] text-zinc-600 uppercase tracking-widest mb-1 font-medium">Cast</p>
                  <p className="text-sm text-zinc-300">{movie.top_cast.slice(0, 4).join(" · ")}</p>
                </div>
              )}
            </div>

            {/* Actions */}
            {isAuthenticated && (
              <div className="flex flex-wrap items-center gap-4">
                <div>
                  <p className="text-[10px] text-zinc-600 uppercase tracking-widest mb-2 font-medium">Your Rating</p>
                  <StarRating movieId={movieId} size="lg" />
                </div>
                <button
                  onClick={() => toggle(movieId)}
                  className={cn(
                    "flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm transition-all duration-200",
                    inWatchlist
                      ? "text-white"
                      : "text-white hover:border-white/20"
                  )}
                  style={{
                    background: inWatchlist ? "var(--brand)" : "rgba(255,255,255,0.08)",
                    border: `1px solid ${inWatchlist ? "transparent" : "rgba(255,255,255,0.1)"}`,
                  }}
                >
                  {inWatchlist
                    ? <><BookmarkCheck className="w-4 h-4" /> In Watchlist</>
                    : <><Bookmark className="w-4 h-4" /> Add to Watchlist</>
                  }
                </button>
              </div>
            )}
          </div>
        </div>

        {/* AI Insights row */}
        {(movie.keywords.length > 0 || movie.mood_tags.length > 0) && (
          <div className="mt-12 rounded-2xl p-6 border border-white/5"
            style={{ background: "var(--surface-card)" }}>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-6 h-6 rounded-lg flex items-center justify-center"
                style={{ background: "rgba(229,9,20,0.12)" }}>
                <Sparkles className="w-3.5 h-3.5 text-brand" />
              </div>
              <h3 className="text-sm font-bold text-white">AI Insights</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {[...movie.mood_tags, ...movie.keywords.slice(0, 10)].map(tag => (
                <span key={tag}
                  className="flex items-center gap-1 text-[11px] px-2.5 py-1 rounded-full font-medium"
                  style={{ background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.5)", border: "1px solid rgba(255,255,255,0.08)" }}>
                  <Tag className="w-2.5 h-2.5" />{tag}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Similar movies */}
        <div className="mt-14">
          <MovieCarousel
            title="More Like This"
            subtitle={similar?.[0]?.shared_attributes?.[0] ? `Based on ${similar[0].shared_attributes[0]}` : "Content-based similarity"}
            movies={similarCards}
            isLoading={similarLoading}
            emptyMessage="No similar movies found"
          />
        </div>
      </div>
    </div>
  );
}

function MovieDetailSkeleton() {
  return (
    <div className="min-h-screen" style={{ background: "var(--surface)" }}>
      <Navbar />
      <div className="h-[65vh] skeleton" />
      <div className="px-5 md:px-8 lg:px-12 py-8 space-y-4 max-w-screen-xl mx-auto">
        <div className="flex gap-8">
          <div className="w-52 aspect-[2/3] skeleton rounded-2xl shrink-0" />
          <div className="flex-1 space-y-4 pt-32">
            <div className="h-12 skeleton rounded-2xl w-3/4" />
            <div className="h-4 skeleton rounded-full w-1/3" />
            <div className="flex gap-2">
              {[60,80,70,90].map(w => <div key={w} className="h-6 skeleton rounded-full" style={{width:w}} />)}
            </div>
            <div className="h-20 skeleton rounded-xl" />
          </div>
        </div>
      </div>
    </div>
  );
}
