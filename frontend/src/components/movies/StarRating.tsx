"use client";
// src/components/movies/StarRating.tsx
import { useState } from "react";
import { Star } from "lucide-react";
import { cn } from "@/lib/utils";
import { useRatings } from "@/hooks";
import { useAuthStore } from "@/store/authStore";

interface Props {
  movieId: number;
  size?: "sm" | "md" | "lg";
  readOnly?: boolean;
  className?: string;
}

const SIZES = {
  sm: "w-4 h-4",
  md: "w-5 h-5",
  lg: "w-6 h-6",
};

export default function StarRating({ movieId, size = "sm", readOnly = false, className }: Props) {
  const { isAuthenticated } = useAuthStore();
  const { ratingMap, rate } = useRatings();
  const currentScore = ratingMap.get(movieId) ?? 0;

  const [hoverScore, setHoverScore] = useState(0);
  const [saving, setSaving] = useState(false);

  const displayScore = hoverScore || currentScore;

  const handleClick = async (score: number) => {
    if (!isAuthenticated || readOnly || saving) return;
    setSaving(true);
    try {
      await rate(movieId, score);
    } finally {
      setSaving(false);
    }
  };

  const handleMouseEnter = (starIndex: number, half: boolean) => {
    if (readOnly) return;
    setHoverScore(half ? starIndex - 0.5 : starIndex);
  };

  return (
    <div
      className={cn("flex items-center gap-0.5", className)}
      onMouseLeave={() => setHoverScore(0)}
    >
      {[1, 2, 3, 4, 5].map(star => {
        const filled = displayScore >= star;
        const half = !filled && displayScore >= star - 0.5;

        return (
          <div key={star} className="relative">
            {/* Half-star left zone */}
            {!readOnly && (
              <div
                className="absolute inset-y-0 left-0 w-1/2 cursor-pointer z-10"
                onMouseEnter={() => handleMouseEnter(star, true)}
                onClick={() => handleClick(star - 0.5)}
              />
            )}
            {/* Full-star right zone */}
            {!readOnly && (
              <div
                className="absolute inset-y-0 right-0 w-1/2 cursor-pointer z-10"
                onMouseEnter={() => handleMouseEnter(star, false)}
                onClick={() => handleClick(star)}
              />
            )}

            <Star
              className={cn(
                SIZES[size],
                "transition-colors duration-100",
                filled
                  ? "fill-accent-gold text-accent-gold"
                  : half
                    ? "fill-accent-gold/50 text-accent-gold"
                    : "fill-transparent text-white/30",
                !readOnly && "hover:scale-110"
              )}
            />
          </div>
        );
      })}
      {currentScore > 0 && (
        <span className="text-xs text-text-muted ml-1">{currentScore.toFixed(1)}</span>
      )}
    </div>
  );
}
