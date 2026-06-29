"use client";
// src/app/(main)/profile/page.tsx
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { User, RefreshCw, Star, Bookmark, Brain, BarChart3, Trash2 } from "lucide-react";
import Navbar from "@/components/layout/Navbar";
import TasteChart from "@/components/profile/TasteChart";
import HybridWeightsDisplay from "@/components/profile/HybridWeightsDisplay";
import { useTasteProfile, useRatings, useWatchlist } from "@/hooks";
import { useAuthStore } from "@/store/authStore";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function ProfilePage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuthStore();
  const { data: profile, isLoading, mutate } = useTasteProfile();
  const { ratings, resetAllRatings } = useRatings();
  const { watchlist } = useWatchlist();

  const [confirming, setConfirming] = useState(false);
  const [resetting, setResetting] = useState(false);

  const handleRefresh = async () => {
    await api.profile.refreshTaste();
    mutate();
  };

  const handleReset = async () => {
    if (!confirming) {
      setConfirming(true);
      // Auto-cancel confirmation after 4 seconds
      setTimeout(() => setConfirming(false), 4000);
      return;
    }
    setResetting(true);
    setConfirming(false);
    try {
      await resetAllRatings();
      mutate();
      router.push("/movies");
      router.refresh();
    } finally {
      setResetting(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <div className="text-center">
          <User className="w-12 h-12 text-brand mx-auto mb-4" />
          <h2 className="text-xl font-bold mb-2">Sign in to see your taste profile</h2>
          <Link href="/login" className="btn-primary mt-4 inline-block">Sign in</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-surface">
      <Navbar />
      <main className="pt-24 pb-16 px-6 md:px-12 max-w-screen-xl mx-auto">

        {/* Header */}
        <div className="flex items-center justify-between mb-10">
          <div>
            <h1 className="text-3xl font-black mb-1">Taste Profile</h1>
            <p className="text-text-secondary">
              Your AI-computed taste fingerprint — powers your recommendations
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleReset}
              disabled={resetting}
              className={cn(
                "flex items-center gap-2 text-sm px-4 py-2 rounded-xl border transition-all duration-200",
                confirming
                  ? "bg-red-500/20 border-red-500/50 text-red-400 animate-pulse"
                  : "bg-white/5 border-white/10 text-text-secondary hover:text-red-400 hover:border-red-500/30",
                resetting && "opacity-50 cursor-not-allowed"
              )}
            >
              <Trash2 className="w-4 h-4" />
              {resetting
                ? "Resetting..."
                : confirming
                ? "Tap again to confirm"
                : "Reset Ratings"}
            </button>
            <button
              onClick={handleRefresh}
              className="btn-ghost flex items-center gap-2 text-sm"
            >
              <RefreshCw className="w-4 h-4" /> Recompute
            </button>
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
          {[
            { icon: Star, label: "Movies rated", value: profile?.total_ratings ?? ratings.length, colour: "text-accent-gold" },
            { icon: Bookmark, label: "In watchlist", value: watchlist.length, colour: "text-brand" },
            { icon: Brain, label: "Top genres", value: profile?.top_genres.length ?? 0, colour: "text-cyan-400" },
            { icon: BarChart3, label: "Recommendations", value: profile?.has_enough_data ? "Active" : "Need 5+ ratings", colour: "text-green-400" },
          ].map(({ icon: Icon, label, value, colour }) => (
            <div key={label} className="bg-surface-card rounded-2xl p-5 border border-white/5">
              <Icon className={cn("w-5 h-5 mb-3", colour)} />
              <p className="text-2xl font-black mb-1">{value}</p>
              <p className="text-xs text-text-muted">{label}</p>
            </div>
          ))}
        </div>

        {isLoading ? (
          <div className="grid md:grid-cols-2 gap-6">
            {[1, 2].map(i => <div key={i} className="h-72 skeleton rounded-2xl" />)}
          </div>
        ) : !profile?.has_enough_data ? (
          <div className="text-center py-20 bg-surface-card rounded-3xl border border-white/5">
            <Brain className="w-12 h-12 text-brand mx-auto mb-4 opacity-50" />
            <h3 className="text-lg font-semibold mb-2">Build your taste profile</h3>
            <p className="text-text-secondary text-sm mb-6 max-w-sm mx-auto">
              Rate at least 5 movies to generate your AI taste profile and unlock
              personalised recommendations
            </p>
            <Link href="/movies" className="btn-primary">Rate some movies</Link>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-6">

            {/* Genre Radar Chart */}
            <div className="bg-surface-card rounded-2xl p-6 border border-white/5">
              <h2 className="text-lg font-bold mb-1">Genre Affinity</h2>
              <p className="text-text-muted text-sm mb-4">
                Computed from your ratings — higher = stronger preference
              </p>
              <TasteChart profile={profile} />
            </div>

            {/* Hybrid weights */}
            <div className="bg-surface-card rounded-2xl p-6 border border-white/5">
              <h2 className="text-lg font-bold mb-1">Recommendation Engine Weights</h2>
              <p className="text-text-muted text-sm mb-5">
                How your recommendations are generated — adapts to your feedback
              </p>
              <HybridWeightsDisplay weights={profile.hybrid_weights} />
            </div>

            {/* Top Directors */}
            {profile.top_directors.length > 0 && (
              <div className="bg-surface-card rounded-2xl p-6 border border-white/5">
                <h2 className="text-lg font-bold mb-4">Favourite Directors</h2>
                <div className="space-y-3">
                  {Object.entries(profile.director_affinities).slice(0, 5).map(([dir, score]) => (
                    <div key={dir} className="flex items-center justify-between">
                      <span className="text-sm font-medium">{dir}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-1.5 bg-white/10 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-brand rounded-full"
                            style={{ width: `${Math.round(score * 100)}%` }}
                          />
                        </div>
                        <span className="text-xs text-text-muted w-8 text-right">
                          {Math.round(score * 100)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Mood tags */}
            {Object.keys(profile.mood_tag_weights).length > 0 && (
              <div className="bg-surface-card rounded-2xl p-6 border border-white/5">
                <h2 className="text-lg font-bold mb-4">Mood Preferences</h2>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(profile.mood_tag_weights)
                    .sort(([, a], [, b]) => b - a)
                    .slice(0, 12)
                    .map(([tag, weight]) => (
                      <span
                        key={tag}
                        className="tag text-sm"
                        style={{
                          background: `rgba(229,9,20,${weight * 0.3})`,
                          color: `rgba(255,255,255,${0.5 + weight * 0.5})`,
                          border: `1px solid rgba(229,9,20,${weight * 0.4})`,
                        }}
                      >
                        {tag}
                      </span>
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
