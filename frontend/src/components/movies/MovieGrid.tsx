"use client";
// src/components/movies/MovieGrid.tsx
import MovieCard from "./MovieCard";
import MovieCardSkeleton from "./MovieCardSkeleton";
import type { MovieCard as MovieCardType } from "@/types";

interface Props {
  movies: MovieCardType[];
  isLoading?: boolean;
  skeletonCount?: number;
  showRating?: boolean;
  emptySlot?: React.ReactNode;
}

export default function MovieGrid({
  movies, isLoading = false, skeletonCount = 18, showRating = false, emptySlot,
}: Props) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 md:gap-4">
        {Array.from({ length: skeletonCount }).map((_, i) => (
          <MovieCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (!movies.length && emptySlot) return <>{emptySlot}</>;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 md:gap-4">
      {movies.map((movie, i) => (
        <MovieCard
          key={movie.tmdb_id}
          movie={movie}
          showRating={showRating}
          priority={i < 6}
        />
      ))}
    </div>
  );
}
