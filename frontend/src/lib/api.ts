import type {
  LoginRequest,
  MovieCard,
  MovieDetail,
  Rating,
  Recommendation,
  RegisterRequest,
  SearchFilters,
  SimilarMovie,
  TasteProfile,
  TokenResponse,
  User,
  WatchlistItem,
  FeedbackAction,
} from "@/types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8001/api/v1";

let _accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  _accessToken = token;
}

export function getAccessToken(): string | null {
  return _accessToken;
}

interface FetchOptions extends RequestInit {
  skipAuth?: boolean;
}

async function apiFetch<T>(
  path: string,
  options: FetchOptions = {}
): Promise<T> {
  const { skipAuth = false, ...init } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((init.headers as Record<string, string>) ?? {}),
  };

  if (!skipAuth && _accessToken) {
    headers["Authorization"] = `Bearer ${_accessToken}`;
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });

  if (
    response.status === 401 &&
    !skipAuth &&
    path !== "/auth/refresh"
  ) {
    const refreshed = await tryRefreshToken();

    if (refreshed) {
      headers["Authorization"] = `Bearer ${_accessToken}`;

      const retryResponse = await fetch(`${BASE_URL}${path}`, {
        ...init,
        headers,
        credentials: "include",
      });

      if (retryResponse.ok) {
        if (retryResponse.status === 204) return undefined as T;
        return retryResponse.json() as Promise<T>;
      }
    }

    setAccessToken(null);

    if (typeof window !== "undefined") {
      window.dispatchEvent(new Event("auth:logout"));
    }

    throw { detail: "Session expired", error_code: "UNAUTHORIZED" };
  }

  if (response.status === 204) return undefined as T;

  const data = await response.json();

  if (!response.ok) throw data;

  return data as T;
}

async function tryRefreshToken(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    });
    if (!res.ok) return false;
    const data: TokenResponse = await res.json();
    setAccessToken(data.access_token);
    return true;
  } catch {
    return false;
  }
}

export const api = {
  auth: {
    register: (body: RegisterRequest) =>
      apiFetch<User>("/auth/register", {
        method: "POST",
        body: JSON.stringify(body),
        skipAuth: true,
      }),

    login: (body: LoginRequest) =>
      apiFetch<TokenResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify(body),
        skipAuth: true,
      }),

    refresh: () =>
      apiFetch<TokenResponse>("/auth/refresh", {
        method: "POST",
        skipAuth: true,
      }),

    logout: () =>
      apiFetch<void>("/auth/logout", { method: "POST" }),

    me: () => apiFetch<User>("/auth/me"),
  },

  movies: {
    trending: (page = 1) =>
      apiFetch<MovieCard[]>(`/movies/trending?page=${page}`),

    popular: (page = 1) =>
      apiFetch<MovieCard[]>(`/movies/popular?page=${page}`),

    topRated: (page = 1) =>
      apiFetch<MovieCard[]>(`/movies/top-rated?page=${page}`),

    detail: (id: number) =>
      apiFetch<MovieDetail>(`/movies/${id}`),

    similar: (id: number, topK = 20) =>
      apiFetch<SimilarMovie[]>(`/movies/${id}/similar?top_k=${topK}`),
  },

  search: {
    keyword: (q: string, filters?: SearchFilters) => {
      const params = new URLSearchParams({ q });
      if (filters?.genres) filters.genres.forEach((g) => params.append("genre", g));
      if (filters?.year_min) params.set("year_min", String(filters.year_min));
      if (filters?.year_max) params.set("year_max", String(filters.year_max));
      if (filters?.rating_min) params.set("rating_min", String(filters.rating_min));
      if (filters?.language) params.set("language", filters.language);
      if (filters?.page) params.set("page", String(filters.page));
      return apiFetch<MovieCard[]>(`/search?${params}`);
    },

    semantic: (query: string, topK = 20, filters?: SearchFilters) =>
      apiFetch<MovieCard[]>("/search/semantic", {
        method: "POST",
        body: JSON.stringify({ query, top_k: topK, filters }),
      }),
  },

  recommendations: {
    get: (topK = 20) =>
      apiFetch<Recommendation[]>(`/recommendations?top_k=${topK}`),

    feedback: (recommendation_id: string, action: FeedbackAction) =>
      apiFetch<void>("/recommendations/feedback", {
        method: "POST",
        body: JSON.stringify({ recommendation_id, action }),
      }),

    refresh: () =>
      apiFetch<Recommendation[]>("/recommendations/refresh", { method: "POST" }),
  },

  ratings: {
    rate: (movie_id: number, score: number) =>
      apiFetch<Rating>("/ratings", {
        method: "POST",
        body: JSON.stringify({ movie_id, score }),
      }),

    mine: () => apiFetch<Rating[]>("/ratings/me"),

    delete: (movie_id: number) =>
      apiFetch<void>(`/ratings/${movie_id}`, { method: "DELETE" }),

    deleteAll: () =>
      apiFetch<void>("/ratings/reset", { method: "DELETE" }),
  },

  watchlist: {
    get: () => apiFetch<WatchlistItem[]>("/watchlist"),

    add: (movie_id: number) =>
      apiFetch<WatchlistItem>("/watchlist", {
        method: "POST",
        body: JSON.stringify({ movie_id }),
      }),

    markWatched: (movie_id: number, watched: boolean) =>
      apiFetch<void>(`/watchlist/${movie_id}`, {
        method: "PATCH",
        body: JSON.stringify({ watched }),
      }),

    remove: (movie_id: number) =>
      apiFetch<void>(`/watchlist/${movie_id}`, { method: "DELETE" }),
  },

  profile: {
    taste: () => apiFetch<TasteProfile>("/profile/taste"),

    refreshTaste: () =>
      apiFetch<void>("/profile/taste/refresh", { method: "POST" }),
  },
};
