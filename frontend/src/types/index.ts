// src/types/index.ts
// Single source of truth for all domain types.
// These mirror the backend Pydantic schemas — keep in sync.

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

// ── Movie ─────────────────────────────────────────────────────────────────────

export interface MovieCard {
  tmdb_id: number;
  title: string;
  poster_url: string | null;
  backdrop_url: string | null;
  vote_average: number;
  year: number | null;
  genres: string[];
  runtime: number | null;
  popularity_score: number;
}

export interface MovieDetail extends MovieCard {
  overview: string | null;
  tagline: string | null;
  vote_count: number;
  popularity: number;
  original_language: string | null;
  director: string | null;
  top_cast: string[];
  mood_tags: string[];
  keywords: string[];
  release_date: string | null;
}

export interface SearchFilters {
  genres?: string[];
  year_min?: number;
  year_max?: number;
  rating_min?: number;
  language?: string;
  runtime_max?: number;
  mood_tags?: string[];
  page?: number;
}

// ── Recommendations ───────────────────────────────────────────────────────────

export interface ScoreBreakdown {
  semantic: number;
  content: number;
  collaborative: number;
  popularity: number;
  composite: number;
}

export interface Recommendation {
  recommendation_id: string;
  movie: MovieCard;
  score: ScoreBreakdown;
  reasons: string[];
  confidence: number;
  match_label: string;
}

export interface SimilarMovie {
  movie: MovieCard;
  similarity_score: number;
  shared_attributes: string[];
}

export type FeedbackAction = "liked" | "dismissed" | "clicked" | "watchlisted";

// ── Ratings ───────────────────────────────────────────────────────────────────

export interface Rating {
  id: string;
  movie_id: number;
  score: number;
  created_at: string;
}

// ── Watchlist ─────────────────────────────────────────────────────────────────

export interface WatchlistItem {
  id: string;
  movie: MovieCard;
  watched: boolean;
  added_at: string;
}

// ── Profile ───────────────────────────────────────────────────────────────────

export interface TasteProfile {
  user_id: string;
  genre_weights: Record<string, number>;
  director_affinities: Record<string, number>;
  mood_tag_weights: Record<string, number>;
  hybrid_weights: {
    semantic: number;
    content: number;
    collaborative: number;
    popularity: number;
  };
  total_ratings: number;
  top_genres: string[];
  top_directors: string[];
  has_enough_data: boolean;
}

// ── UI Helpers ────────────────────────────────────────────────────────────────

export interface ApiError {
  detail: string;
  error_code: string;
}

export type LoadingState = "idle" | "loading" | "success" | "error";
