import useSWR, { mutate as globalMutate } from "swr";
import { useCallback, useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

import type {
  FeedbackAction,
  MovieCard,
  MovieDetail,
  Rating,
  Recommendation,
  SearchFilters,
  SimilarMovie,
  TasteProfile,
  WatchlistItem,
} from "@/types";

function toErrorMessage(e: unknown, fallback: string): string {
  if (!e) return fallback;
  if (typeof e === "string") return e;
  if (typeof e === "object") {
    const obj = e as Record<string, unknown>;
    if (Array.isArray(obj.detail)) {
      return obj.detail
        .map((d: unknown) =>
          typeof d === "object" && d !== null
            ? ((d as Record<string, unknown>).msg as string) ?? JSON.stringify(d)
            : String(d)
        )
        .join(", ");
    }
    if (typeof obj.detail === "string") return obj.detail;
    if (typeof obj.message === "string") return obj.message;
  }
  return fallback;
}


// ── Recommendations ───────────────────────────────────────────────────────────

export function useRecommendations(topK = 20) {
  const { user } = useAuthStore();
  const [isRefreshing, setIsRefreshing] = useState(false);

  const swr = useSWR<Recommendation[]>(
    user ? `/recommendations?top_k=${topK}` : null,
    () => api.recommendations.get(topK),
    { revalidateOnFocus: false, dedupingInterval: 60_000 }
  );

  const submitFeedback = useCallback(
    async (recommendation_id: string, action: FeedbackAction) => {
      await api.recommendations.feedback(recommendation_id, action);
      if (action === "dismissed") {
        swr.mutate(
          prev => prev?.filter(r => r.recommendation_id !== recommendation_id),
          { revalidate: false }
        );
      }
    },
    [swr]
  );

  const refresh = useCallback(async () => {
    if (isRefreshing) return;
    setIsRefreshing(true);
    try {
      const fresh = await api.recommendations.refresh();
      swr.mutate(fresh, { revalidate: false });
    } finally {
      setIsRefreshing(false);
    }
  }, [swr, isRefreshing]);

  return {
    recommendations: swr.data ?? [],
    error: swr.error,
    isLoading: swr.isLoading,
    isRefreshing,
    mutate: swr.mutate,
    submitFeedback,
    refresh,
  };
}


// ── Trending ──────────────────────────────────────────────────────────────────

export function useTrending(page = 1) {
  const swr = useSWR<MovieCard[]>(
    `/movies/trending?page=${page}`,
    () => api.movies.trending(page),
    { revalidateOnFocus: false, dedupingInterval: 300_000 }
  );
  return { data: swr.data ?? [], error: swr.error, isLoading: swr.isLoading };
}


// ── Popular ───────────────────────────────────────────────────────────────────

export function usePopular(page = 1) {
  const swr = useSWR<MovieCard[]>(
    `/movies/popular?page=${page}`,
    () => api.movies.popular(page),
    { revalidateOnFocus: false }
  );
  return { data: swr.data ?? [], error: swr.error, isLoading: swr.isLoading };
}


// ── Top Rated ─────────────────────────────────────────────────────────────────

export function useTopRated(page = 1) {
  const swr = useSWR<MovieCard[]>(
    `/movies/top-rated?page=${page}`,
    () => api.movies.topRated(page),
    { revalidateOnFocus: false }
  );
  return { data: swr.data ?? [], error: swr.error, isLoading: swr.isLoading };
}


// ── Movie Detail ──────────────────────────────────────────────────────────────

export function useMovieDetail(id: number) {
  return useSWR<MovieDetail>(
    id ? `/movies/${id}` : null,
    () => api.movies.detail(id),
    { revalidateOnFocus: false }
  );
}


// ── Similar Movies ────────────────────────────────────────────────────────────

export function useSimilarMovies(id: number) {
  return useSWR<SimilarMovie[]>(
    id ? `/movies/${id}/similar` : null,
    () => api.movies.similar(id),
    { revalidateOnFocus: false }
  );
}


// ── Search ────────────────────────────────────────────────────────────────────

export function useSearch() {
  const [results, setResults] = useState<MovieCard[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastQuery, setLastQuery] = useState("");
  const [lastFilters, setLastFilters] = useState<SearchFilters | undefined>();
  const [mode, setMode] = useState<"keyword" | "semantic">("keyword");
  const [currentTopK, setCurrentTopK] = useState(20);

  const search = useCallback(async (
    query: string,
    searchMode: "keyword" | "semantic" = "keyword",
    filters?: SearchFilters
  ) => {
    if (!query.trim()) { setResults([]); return; }
    setIsLoading(true);
    setError(null);
    setLastQuery(query);
    setLastFilters(filters);
    setMode(searchMode);
    setCurrentTopK(20);
    try {
      const data = searchMode === "semantic"
        ? await api.search.semantic(query, 20, filters)
        : await api.search.keyword(query, filters);
      setResults(data);
    } catch (e: unknown) {
      setError(toErrorMessage(e, "Search failed"));
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadMore = useCallback(async () => {
    if (!lastQuery || mode !== "semantic" || isLoadingMore) return;
    const nextTopK = currentTopK + 20;
    setIsLoadingMore(true);
    setError(null);
    try {
      const data = await api.search.semantic(lastQuery, nextTopK, lastFilters);
      setResults(data);
      setCurrentTopK(nextTopK);
    } catch (e: unknown) {
      setError(toErrorMessage(e, "Failed to load more results"));
    } finally {
      setIsLoadingMore(false);
    }
  }, [lastQuery, lastFilters, mode, currentTopK, isLoadingMore]);

  const clear = useCallback(() => {
    setResults([]);
    setLastQuery("");
    setError(null);
    setCurrentTopK(20);
  }, []);

  return { results, isLoading, isLoadingMore, error, lastQuery, mode, search, loadMore, clear };
}


// ── Watchlist ─────────────────────────────────────────────────────────────────

export function useWatchlist() {
  const { user } = useAuthStore();

  const swr = useSWR<WatchlistItem[]>(
    user ? "/watchlist" : null,
    () => api.watchlist.get(),
    { revalidateOnFocus: false }
  );

  const watchlistIds = new Set(swr.data?.map(w => w.movie.tmdb_id) ?? []);

  const add = useCallback(async (movie_id: number) => {
    await api.watchlist.add(movie_id);
    swr.mutate();
  }, [swr]);

  const remove = useCallback(async (movie_id: number) => {
    await api.watchlist.remove(movie_id);
    swr.mutate(
      prev => prev?.filter(w => w.movie.tmdb_id !== movie_id),
      { revalidate: false }
    );
  }, [swr]);

  const toggle = useCallback(async (movie_id: number) => {
    if (watchlistIds.has(movie_id)) {
      await remove(movie_id);
    } else {
      await add(movie_id);
    }
  }, [watchlistIds, add, remove]);

  const markWatched = useCallback(async (movie_id: number, watched: boolean) => {
    await api.watchlist.markWatched(movie_id, watched);
    swr.mutate(
      prev => prev?.map(w => w.movie.tmdb_id === movie_id ? { ...w, watched } : w),
      { revalidate: false }
    );
  }, [swr]);

  return {
    watchlist: swr.data ?? [],
    watchlistIds,
    isLoading: swr.isLoading,
    add,
    remove,
    toggle,
    markWatched,
  };
}


// ── Ratings ───────────────────────────────────────────────────────────────────

export function useRatings() {
  const { user } = useAuthStore();

  const swr = useSWR<Rating[]>(
    user ? "/ratings/me" : null,
    () => api.ratings.mine(),
    { revalidateOnFocus: false }
  );

  const ratingMap = new Map(swr.data?.map(r => [r.movie_id, r.score]) ?? []);

  const rate = useCallback(async (movie_id: number, score: number) => {
    await api.ratings.rate(movie_id, score);
    swr.mutate();
    globalMutate(
      (key: string) => key?.startsWith?.("/recommendations"),
      undefined
    );
  }, [swr]);

  const deleteRating = useCallback(async (movie_id: number) => {
    await api.ratings.delete(movie_id);
    swr.mutate(
      prev => prev?.filter(r => r.movie_id !== movie_id),
      { revalidate: false }
    );
  }, [swr]);

  const resetAllRatings = useCallback(async () => {
    await api.ratings.deleteAll();
    swr.mutate([], { revalidate: false });
    globalMutate(
      (key: string) => key?.startsWith?.("/recommendations"),
      undefined
    );
    globalMutate("/profile/taste", undefined);
  }, [swr]);

  return { ratings: swr.data ?? [], ratingMap, rate, deleteRating, resetAllRatings };
}


// ── Taste Profile ─────────────────────────────────────────────────────────────

export function useTasteProfile() {
  const { user } = useAuthStore();

  return useSWR<TasteProfile>(
    user ? "/profile/taste" : null,
    () => api.profile.taste(),
    { revalidateOnFocus: false }
  );
}