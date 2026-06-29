// src/lib/utils.ts
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatRuntime(minutes: number | null): string {
  if (!minutes) return "";
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

export function formatRating(rating: number): string {
  return rating.toFixed(1);
}

export function formatYear(dateStr: string | null | undefined): string {
  if (!dateStr) return "";
  return dateStr.slice(0, 4);
}

export function confidenceToPercent(confidence: number): number {
  return Math.round(confidence * 100);
}

// Genre → Tailwind colour classes (bg + text)
const GENRE_COLOURS: Record<string, string> = {
  Action:          "bg-red-500/20 text-red-400",
  Adventure:       "bg-orange-500/20 text-orange-400",
  Animation:       "bg-yellow-500/20 text-yellow-400",
  Comedy:          "bg-green-500/20 text-green-400",
  Crime:           "bg-gray-500/20 text-gray-400",
  Documentary:     "bg-blue-500/20 text-blue-400",
  Drama:           "bg-purple-500/20 text-purple-400",
  Fantasy:         "bg-indigo-500/20 text-indigo-400",
  Horror:          "bg-red-900/30 text-red-300",
  Mystery:         "bg-violet-500/20 text-violet-400",
  Romance:         "bg-pink-500/20 text-pink-400",
  "Science Fiction": "bg-cyan-500/20 text-cyan-400",
  Thriller:        "bg-amber-500/20 text-amber-400",
  War:             "bg-stone-500/20 text-stone-400",
  Western:         "bg-yellow-800/20 text-yellow-600",
};

export function genreColour(genre: string): string {
  return GENRE_COLOURS[genre] ?? "bg-white/10 text-white/70";
}

export function scoreToColor(score: number): string {
  if (score >= 0.75) return "text-green-400";
  if (score >= 0.5)  return "text-yellow-400";
  return "text-orange-400";
}

export function ratingToStars(score: number): number[] {
  // score is 0.5–5.0 → return array of 5 star fill values 0|0.5|1
  const full = Math.floor(score);
  const half = score % 1 >= 0.25 ? 0.5 : 0;
  return Array.from({ length: 5 }, (_, i) => {
    if (i < full) return 1;
    if (i === full && half) return 0.5;
    return 0;
  });
}

export function truncate(str: string, length: number): string {
  return str.length > length ? str.slice(0, length) + "…" : str;
}

export const GENRES = [
  "Action", "Adventure", "Animation", "Comedy", "Crime",
  "Documentary", "Drama", "Fantasy", "Horror", "Mystery",
  "Romance", "Science Fiction", "Thriller", "War", "Western",
];

export const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "fr", label: "French" },
  { code: "de", label: "German" },
  { code: "ja", label: "Japanese" },
  { code: "ko", label: "Korean" },
  { code: "es", label: "Spanish" },
  { code: "it", label: "Italian" },
  { code: "hi", label: "Hindi" },
];
