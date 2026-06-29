"use client";
// src/app/page.tsx
import Image from "next/image";
import Link from "next/link";
import { Play, Info, RefreshCw, Sparkles, TrendingUp, Star, ChevronRight, Brain, Search, Zap } from "lucide-react";
import Navbar from "@/components/layout/Navbar";
import MovieCarousel from "@/components/movies/MovieCarousel";
import RecommendationCard from "@/components/recommendations/RecommendationCard";
import { useRecommendations, useTrending, usePopular, useTopRated } from "@/hooks";
import { useAuthStore } from "@/store/authStore";

export default function HomePage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuthStore();
  const { recommendations, isLoading: recsLoading, isRefreshing, submitFeedback, refresh } = useRecommendations(12);
  const { data: trending,  isLoading: trendingLoading  } = useTrending();
  const { data: popular,   isLoading: popularLoading   } = usePopular();
  const { data: topRated,  isLoading: topRatedLoading  } = useTopRated();

  const hero = trending?.[0];

  return (
    <div className="min-h-screen" style={{ background: "var(--surface)" }}>
      <Navbar />

      {/* ── Hero ─────────────────────────────────────────────────────── */}
      <section className="relative h-[80vh] min-h-[560px] max-h-[860px] overflow-hidden">

        {hero?.backdrop_url ? (
          <Image
            src={hero.backdrop_url}
            alt={hero.title}
            fill priority
            className="object-cover"
            sizes="100vw"
          />
        ) : (
          <div className="absolute inset-0 bg-gradient-to-br from-zinc-900 via-zinc-950 to-black" />
        )}

        <div className="absolute inset-0 overlay-left" />
        <div className="absolute inset-0 overlay-bottom" />
        <div className="absolute inset-0 overlay-vignette" />

        <div className="absolute inset-0 flex items-end pb-20 px-5 md:px-8 lg:px-12 max-w-screen-2xl mx-auto">
          <div className="max-w-xl animate-slide-up">
            {hero ? (
              <>
                <div className="flex items-center gap-2 mb-4">
                  <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold"
                    style={{ background: "rgba(229,9,20,0.15)", color: "#E50914" }}>
                    <TrendingUp className="w-3 h-3" />
                    Trending Now
                  </div>
                </div>

                <h1 className="text-5xl md:text-6xl font-black tracking-tight leading-none mb-4 text-white"
                  style={{ textShadow: "0 2px 20px rgba(0,0,0,0.5)" }}>
                  {hero.title}
                </h1>

                <div className="flex items-center gap-3 mb-6">
                  {hero.year && (
                    <span className="text-sm text-zinc-400 font-medium">{hero.year}</span>
                  )}
                  <div className="flex items-center gap-1">
                    <Star className="w-3.5 h-3.5 fill-yellow-400 text-yellow-400" />
                    <span className="text-sm font-semibold text-white">{hero.vote_average.toFixed(1)}</span>
                  </div>
                  {hero.genres.slice(0, 3).map(g => (
                    <span key={g} className="text-xs text-zinc-400 px-2 py-0.5 rounded-full border border-white/10 bg-white/5">
                      {g}
                    </span>
                  ))}
                </div>

                <div className="flex gap-3">
                  <Link href={`/movies/${hero.tmdb_id}`} className="btn-primary">
                    <Play className="w-4 h-4 fill-white" /> View Details
                  </Link>
                  <Link href={`/movies/${hero.tmdb_id}`} className="btn-ghost">
                    <Info className="w-4 h-4" /> More Info
                  </Link>
                </div>
              </>
            ) : (
              <div className="space-y-4 animate-pulse">
                <div className="h-4 skeleton rounded-full w-32" />
                <div className="h-14 skeleton rounded-2xl w-96" />
                <div className="h-4 skeleton rounded-full w-48" />
                <div className="flex gap-3">
                  <div className="h-11 skeleton rounded-xl w-36" />
                  <div className="h-11 skeleton rounded-xl w-28" />
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* ── Main content ──────────────────────────────────────────────── */}
      <div className="relative z-10 -mt-6 space-y-14 px-5 md:px-8 lg:px-12 pb-20 max-w-screen-2xl mx-auto">

        {/* ── AI Recommendations ────────────────────────────────────── */}
        {isAuthenticated && (
          <section>
            <div className="flex items-center justify-between mb-6">
              <div>
                <div className="flex items-center gap-2.5 mb-1">
                  <div className="w-6 h-6 rounded-lg flex items-center justify-center"
                    style={{ background: "rgba(229,9,20,0.15)" }}>
                    <Sparkles className="w-3.5 h-3.5 text-brand" />
                  </div>
                  <h2 className="text-xl font-bold text-white tracking-tight">
                    {user?.username ? `${user.username}'s picks` : "For you"}
                  </h2>
                </div>
                <p className="text-sm text-zinc-500 ml-8">
                  Personalised · Semantic AI · Hybrid engine
                </p>
              </div>

              {/* FIX: disabled + spinner while refreshing */}
              <button
                onClick={refresh}
                disabled={isRefreshing}
                className="btn-ghost text-sm py-2 px-3 gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
                {isRefreshing ? "Refreshing..." : "Refresh"}
              </button>
            </div>

            {recsLoading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="rounded-2xl overflow-hidden animate-pulse border border-white/5"
                    style={{ background: "var(--surface-card)" }}>
                    <div className="aspect-video skeleton" />
                    <div className="p-4 space-y-2.5">
                      <div className="h-4 skeleton rounded-lg w-3/4" />
                      <div className="h-3 skeleton rounded-lg w-1/2" />
                      <div className="h-3 skeleton rounded-lg w-2/3" />
                    </div>
                  </div>
                ))}
              </div>
            ) : recommendations.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {recommendations.map(rec => (
                  <RecommendationCard
                    key={rec.recommendation_id}
                    rec={rec}
                    onFeedback={submitFeedback}
                  />
                ))}
              </div>
            ) : (
              <div className="rounded-2xl border border-white/5 p-10 text-center"
                style={{ background: "var(--surface-card)" }}>
                <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
                  style={{ background: "rgba(229,9,20,0.1)" }}>
                  <Sparkles className="w-7 h-7 text-brand" />
                </div>
                <h3 className="text-lg font-bold mb-2">Rate movies to unlock AI recommendations</h3>
                <p className="text-sm text-zinc-500 max-w-sm mx-auto mb-6">
                  Rate at least 5 movies and our AI will learn your taste and generate personalised picks
                </p>
                <Link href="/movies" className="btn-primary">
                  Browse Movies
                </Link>
              </div>
            )}
          </section>
        )}

        {/* ── Trending ──────────────────────────────────────────────── */}
        <MovieCarousel
          title="Trending This Week"
          subtitle="What everyone's watching right now"
          movies={trending ?? []}
          isLoading={trendingLoading}
          viewAllHref="/movies"
        />

        {/* ── Top Rated ─────────────────────────────────────────────── */}
        <MovieCarousel
          title="Top Rated"
          subtitle="Critically acclaimed masterpieces"
          movies={topRated ?? []}
          isLoading={topRatedLoading}
          viewAllHref="/movies"
        />

        {/* ── Popular ───────────────────────────────────────────────── */}
        <MovieCarousel
          title="Popular Right Now"
          subtitle="Most watched globally"
          movies={popular ?? []}
          isLoading={popularLoading}
          showRating
          viewAllHref="/movies"
        />

        {/* ── CTA — unauthenticated ─────────────────────────────────── */}
        {!authLoading && !isAuthenticated && (
          <section className="relative overflow-hidden rounded-3xl p-10 md:p-16 text-center"
            style={{
              background: "linear-gradient(135deg, rgba(229,9,20,0.08) 0%, rgba(139,92,246,0.08) 100%)",
              border: "1px solid rgba(255,255,255,0.06)"
            }}
          >
            <div className="absolute inset-0 pointer-events-none" style={{
              background: "radial-gradient(ellipse at 50% 100%, rgba(229,9,20,0.08) 0%, transparent 70%)"
            }} />

            <div className="relative">
              <div className="flex flex-wrap items-center justify-center gap-2 mb-8">
                {[
                  { icon: Brain, label: "AI Taste Profile" },
                  { icon: Search, label: "Semantic Search" },
                  { icon: Zap,   label: "Hybrid Engine" },
                ].map(({ icon: Icon, label }) => (
                  <div
                    key={label}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-zinc-300"
                    style={{ background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.08)" }}
                  >
                    <Icon className="w-3 h-3 text-brand" />
                    {label}
                  </div>
                ))}
              </div>

              <h2 className="text-4xl md:text-5xl font-black mb-4 tracking-tight">
                Your AI movie companion
              </h2>
              <p className="text-zinc-400 max-w-lg mx-auto mb-8 text-base leading-relaxed">
                Semantic search, personalised recommendations, and explainable AI —
                built for people who take movies seriously.
              </p>

              <div className="flex flex-wrap gap-3 justify-center">
                <Link href="/register" className="btn-primary px-8 py-3 text-base">
                  Get started free
                </Link>
                <Link href="/search" className="btn-ghost px-8 py-3 text-base">
                  Explore movies <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
