"use client";
// src/components/recommendations/RecommendationCard.tsx
import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import { ThumbsUp, ThumbsDown, Bookmark, Star, ChevronDown, ChevronUp, Sparkles } from "lucide-react";
import { cn, confidenceToPercent, formatRuntime, genreColour } from "@/lib/utils";
import type { Recommendation } from "@/types";
import ScoreBreakdownBar from "./ScoreBreakdownBar";

interface Props {
  rec: Recommendation;
  onFeedback: (id: string, action: "liked" | "dismissed" | "watchlisted" | "clicked") => void;
  className?: string;
}

const LABEL_STYLES: Record<string, { text: string; bg: string; dot: string }> = {
  "Perfect match":          { text: "#4ade80", bg: "rgba(74,222,128,0.12)",  dot: "#4ade80" },
  "Great pick":             { text: "#60a5fa", bg: "rgba(96,165,250,0.12)",  dot: "#60a5fa" },
  "You might like":         { text: "#facc15", bg: "rgba(250,204,21,0.12)",  dot: "#facc15" },
  "Worth a try":            { text: "#fb923c", bg: "rgba(251,146,60,0.12)",  dot: "#fb923c" },
  "Discovering something new": { text: "#c084fc", bg: "rgba(192,132,252,0.12)", dot: "#c084fc" },
  "Popular pick":           { text: "#94a3b8", bg: "rgba(148,163,184,0.12)", dot: "#94a3b8" },
};

export default function RecommendationCard({ rec, onFeedback, className }: Props) {
  const [showDetails, setShowDetails] = useState(false);
  const [dismissed,   setDismissed]   = useState(false);
  const [liked,       setLiked]       = useState(false);
  const [saved,       setSaved]       = useState(false);

  if (dismissed) return null;

  const { movie, score, reasons, confidence, match_label, recommendation_id } = rec;
  const pct = confidenceToPercent(confidence);
  const labelStyle = LABEL_STYLES[match_label] ?? LABEL_STYLES["Popular pick"];

  const handleDismiss = () => {
    setDismissed(true);
    onFeedback(recommendation_id, "dismissed");
  };

  const handleLike = () => {
    setLiked(true);
    onFeedback(recommendation_id, "liked");
  };

  const handleSave = () => {
    setSaved(true);
    onFeedback(recommendation_id, "watchlisted");
  };

  return (
    <div
      className={cn(
        "group relative rounded-2xl overflow-hidden",
        "border transition-all duration-400",
        "hover:-translate-y-1 hover:border-[var(--brand)]",
        className
      )}
      style={{
        background: "var(--surface-card)",
        borderColor: "rgba(255,255,255,0.06)",
      }}
    >
      {/* Backdrop image */}
      <Link
        href={`/movies/${movie.tmdb_id}`}
        onClick={() => onFeedback(recommendation_id, "clicked")}
      >
        <div className="relative aspect-[16/9] overflow-hidden">
          {movie.backdrop_url || movie.poster_url ? (
            <Image
              src={movie.backdrop_url ?? movie.poster_url!}
              alt={movie.title}
              fill
              sizes="(max-width: 640px) 100vw, 50vw"
              className="object-cover transition-transform duration-500 group-hover:scale-105"
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center" style={{ background: "var(--surface-raised)" }}>
              <span className="text-5xl opacity-30">🎬</span>
            </div>
          )}

          {/* Gradient */}
          <div className="absolute inset-0" style={{
            background: "linear-gradient(to top, rgba(17,17,17,1) 0%, rgba(17,17,17,0.3) 50%, transparent 100%)"
          }} />

          {/* Match label */}
          <div className="absolute top-3 left-3">
            <div
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold"
              style={{ background: labelStyle.bg, color: labelStyle.text }}
            >
              <div
                className="w-1.5 h-1.5 rounded-full"
                style={{ background: labelStyle.dot }}
              />
              {match_label}
            </div>
          </div>

          {/* Confidence */}
          <div className="absolute top-3 right-3 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/60 backdrop-blur-md border border-white/10">
            <Sparkles className="w-2.5 h-2.5 text-brand" />
            <span className="text-[11px] font-bold text-white">{pct}%</span>
          </div>
        </div>
      </Link>

      {/* Content */}
      <div className="p-4">
        {/* Title + meta */}
        <div className="mb-3">
          <Link href={`/movies/${movie.tmdb_id}`}>
            <h3 className="font-bold text-[15px] leading-tight line-clamp-1 text-white hover:text-zinc-300 transition-colors">
              {movie.title}
            </h3>
          </Link>
          <div className="flex items-center gap-2 mt-1">
            {movie.year && <span className="text-[11px] text-zinc-500">{movie.year}</span>}
            {movie.runtime && (
              <>
                <span className="text-zinc-700">·</span>
                <span className="text-[11px] text-zinc-500">{formatRuntime(movie.runtime)}</span>
              </>
            )}
            <span className="text-zinc-700">·</span>
            <span className="flex items-center gap-1">
              <Star className="w-2.5 h-2.5 fill-yellow-400 text-yellow-400" />
              <span className="text-[11px] text-zinc-400 font-medium">{movie.vote_average.toFixed(1)}</span>
            </span>
          </div>
        </div>

        {/* Genres */}
        {movie.genres.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {movie.genres.slice(0, 3).map(g => (
              <span key={g} className={cn("tag", genreColour(g))} style={{ fontSize: "9px" }}>
                {g}
              </span>
            ))}
          </div>
        )}

        {/* AI Reasons */}
        {reasons.length > 0 && (
          <div className="space-y-1.5 mb-3">
            {reasons.slice(0, 3).map((reason, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="text-brand text-[10px] mt-0.5 shrink-0 font-bold">✦</span>
                <span className="text-[11px] text-zinc-400 leading-relaxed">{reason}</span>
              </div>
            ))}
          </div>
        )}

        {/* Score breakdown toggle */}
        <button
          onClick={() => setShowDetails(v => !v)}
          className="flex items-center gap-1.5 text-[11px] text-zinc-600 hover:text-zinc-300 transition-colors mb-3 group/toggle"
        >
          <div className="w-3.5 h-3.5 rounded border border-zinc-700 group-hover/toggle:border-zinc-500 flex items-center justify-center transition-colors">
            {showDetails
              ? <ChevronUp className="w-2.5 h-2.5" />
              : <ChevronDown className="w-2.5 h-2.5" />
            }
          </div>
          {showDetails ? "Hide" : "Show"} score breakdown
        </button>

        {showDetails && (
          <div className="mb-3 animate-slide-up">
            <ScoreBreakdownBar score={score} />
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 pt-3 border-t border-white/5">
          <button
            onClick={handleLike}
            disabled={liked}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all duration-200",
              liked
                ? "bg-green-500/20 text-green-400 cursor-default"
                : "bg-white/5 text-zinc-400 hover:bg-green-500/15 hover:text-green-400"
            )}
          >
            <ThumbsUp className="w-3 h-3" />
            {liked ? "Liked" : "Like"}
          </button>

          <button
            onClick={handleDismiss}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 text-zinc-500 text-[11px] font-semibold hover:bg-white/8 hover:text-zinc-300 transition-all duration-200"
          >
            <ThumbsDown className="w-3 h-3" />
            Pass
          </button>

          <button
            onClick={handleSave}
            disabled={saved}
            className={cn(
              "ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-semibold transition-all duration-200",
              saved
                ? "bg-brand/20 text-brand cursor-default"
                : "bg-white/5 text-zinc-400 hover:bg-brand/15 hover:text-brand"
            )}
          >
            <Bookmark className="w-3 h-3" />
            {saved ? "Saved" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
