"""
app/schemas/movie.py + recommendation.py + rating.py + watchlist.py + profile.py
─────────────────────────────────────────────────────────────────────────────────
All domain schemas in one module. Split by domain prefix.
"""

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


# ══════════════════════════════════════════════════════════════════════════════
# Movie Schemas
# ══════════════════════════════════════════════════════════════════════════════

class MovieBase(BaseModel):
    tmdb_id: int
    title: str
    overview: str | None = None
    release_date: date | None = None
    vote_average: float
    vote_count: int
    popularity: float
    poster_path: str | None = None
    backdrop_path: str | None = None
    genres: list[str] = []
    runtime: int | None = None
    original_language: str | None = None

    model_config = {"from_attributes": True}


class MovieCardResponse(BaseModel):
    """Lightweight card view — used in lists and carousels."""
    tmdb_id: int
    title: str
    poster_url: str | None
    backdrop_url: str | None
    vote_average: float
    year: int | None
    genres: list[str]
    runtime: int | None
    popularity_score: float

    model_config = {"from_attributes": True}


class MovieDetailResponse(MovieBase):
    """Full detail view — used on movie detail page."""
    tagline: str | None = None
    director: str | None = None
    top_cast: list[str] = []
    mood_tags: list[str] = []
    keywords: list[str] = []
    poster_url: str | None = None
    backdrop_url: str | None = None
    year: int | None = None

    model_config = {"from_attributes": True}


class MovieSearchFilters(BaseModel):
    """Query params for /search and /movies endpoints."""
    genres: list[str] | None = None
    year_min: int | None = None
    year_max: int | None = None
    rating_min: float | None = Field(None, ge=0, le=10)
    language: str | None = None
    runtime_max: int | None = None
    mood_tags: list[str] | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


# ══════════════════════════════════════════════════════════════════════════════
# Recommendation Schemas
# ══════════════════════════════════════════════════════════════════════════════

class ScoreBreakdown(BaseModel):
    """Per-signal score attribution for explainable AI."""
    semantic: float
    content: float
    collaborative: float
    popularity: float
    composite: float


class RecommendationResponse(BaseModel):
    recommendation_id: uuid.UUID
    movie: MovieCardResponse
    score: ScoreBreakdown
    # Human-readable reasons for the recommendation
    reasons: list[str]
    confidence: float  # 0–1, derived from composite score
    match_label: str   # "Perfect match" | "Great pick" | "You might like"

    model_config = {"from_attributes": True}


class SimilarMovieResponse(BaseModel):
    movie: MovieCardResponse
    similarity_score: float
    shared_attributes: list[str]  # ["Same director", "Sci-Fi", "Mindbending"]


class FeedbackRequest(BaseModel):
    recommendation_id: uuid.UUID
    action: str = Field(pattern="^(liked|dismissed|clicked|watchlisted)$")


class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    top_k: int = Field(20, ge=1, le=50)
    filters: MovieSearchFilters | None = None


# ══════════════════════════════════════════════════════════════════════════════
# Rating Schemas
# ══════════════════════════════════════════════════════════════════════════════

class RatingRequest(BaseModel):
    movie_id: int
    score: float = Field(ge=0.5, le=5.0)

    def normalised_score(self) -> float:
        """Convert 0.5–5.0 scale to 0–1 for ML pipeline."""
        return (self.score - 0.5) / 4.5


class RatingResponse(BaseModel):
    id: uuid.UUID
    movie_id: int
    score: float
    created_at: datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# Watchlist Schemas
# ══════════════════════════════════════════════════════════════════════════════

class WatchlistAddRequest(BaseModel):
    movie_id: int


class WatchlistUpdateRequest(BaseModel):
    watched: bool


class WatchlistResponse(BaseModel):
    id: uuid.UUID
    movie: MovieCardResponse
    watched: bool
    added_at: datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# Profile / Taste Schemas
# ══════════════════════════════════════════════════════════════════════════════

class TasteProfileResponse(BaseModel):
    """User's computed taste profile — powers the dashboard radar chart."""
    user_id: uuid.UUID
    genre_weights: dict[str, float]
    director_affinities: dict[str, float]
    mood_tag_weights: dict[str, float]
    hybrid_weights: dict[str, float]
    total_ratings: int
    top_genres: list[str]        # Top 5 by weight
    top_directors: list[str]     # Top 3 by affinity
    has_enough_data: bool        # False if < 5 ratings (cold start)

    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel):
    """Generic pagination wrapper."""
    items: list[Any]
    total: int
    page: int
    page_size: int
    has_next: bool
