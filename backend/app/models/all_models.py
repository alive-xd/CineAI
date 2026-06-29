"""
app/models/rating.py + watchlist.py + review.py + user_preference.py
+ recommendation.py + movie_embedding.py

All collected in one file to keep imports simple.
Each model is in its own class — split into separate files if the project grows.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ── Rating ─────────────────────────────────────────────────────────────────────

class Rating(Base):
    """
    User movie ratings (0.5–5.0 in 0.5 increments).
    Drives the collaborative filtering matrix.
    """
    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_movie_rating"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey("movies.tmdb_id", ondelete="CASCADE"), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.5–5.0
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="ratings")  # noqa: F821
    movie: Mapped["Movie"] = relationship("Movie", back_populates="ratings")  # noqa: F821


# ── Watchlist ──────────────────────────────────────────────────────────────────

class Watchlist(Base):
    """
    User watchlist. 'watched' flag lets users track completion.
    Also used as an implicit positive signal for collaborative filtering.
    """
    __tablename__ = "watchlist"
    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_movie_watchlist"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey("movies.tmdb_id", ondelete="CASCADE"), nullable=False, index=True)
    watched: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="watchlist")  # noqa: F821
    movie: Mapped["Movie"] = relationship("Movie", back_populates="watchlist_entries")  # noqa: F821


# ── Review ─────────────────────────────────────────────────────────────────────

class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey("movies.tmdb_id", ondelete="CASCADE"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="reviews")  # noqa: F821
    movie: Mapped["Movie"] = relationship("Movie", back_populates="reviews")  # noqa: F821


# ── UserPreference ─────────────────────────────────────────────────────────────

class UserPreference(Base):
    """
    Stores the user's learned taste profile.
    - genre_weights: {"Action": 0.8, "Drama": 0.3, ...}
    - hybrid_weights: current per-user α, β, γ, δ for the hybrid ranker
    - embedding_centroid: 384-dim vector (stored as JSON list) — average of all
      rated movie embeddings weighted by rating score. Used for semantic matching.
    """
    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    genre_weights: Mapped[dict] = mapped_column(JSONB, default=dict)
    director_affinities: Mapped[dict] = mapped_column(JSONB, default=dict)
    mood_tag_weights: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Per-user hybrid ranker weights (α, β, γ, δ)
    hybrid_weights: Mapped[dict] = mapped_column(
        JSONB,
        default=lambda: {
            "semantic": 0.35,
            "content": 0.30,
            "collaborative": 0.25,
            "popularity": 0.10,
        },
    )

    # Flattened 384-dim float list — centroid of all rated-movie embeddings
    embedding_centroid: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    total_ratings: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="preferences")  # noqa: F821


# ── MovieEmbedding ─────────────────────────────────────────────────────────────

class MovieEmbedding(Base):
    """
    Tracks which movies have been embedded and stored in Qdrant.
    The actual vector lives in Qdrant — this table is the index/audit log.
    """
    __tablename__ = "movie_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey("movies.tmdb_id", ondelete="CASCADE"), unique=True, nullable=False)
    qdrant_point_id: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    movie: Mapped["Movie"] = relationship("Movie", back_populates="embedding")  # noqa: F821


# ── Recommendation ─────────────────────────────────────────────────────────────

class Recommendation(Base):
    """
    Persisted recommendation results with full score attribution.
    Storing these enables:
    - Fast retrieval (no recompute on every page load)
    - Feedback collection against specific rec instances
    - A/B testing and quality analysis
    """
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id: Mapped[int] = mapped_column(Integer, ForeignKey("movies.tmdb_id", ondelete="CASCADE"), nullable=False)

    # Composite score (0–1)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    # Individual signal scores for explainability
    semantic_score: Mapped[float] = mapped_column(Float, default=0.0)
    content_score: Mapped[float] = mapped_column(Float, default=0.0)
    collab_score: Mapped[float] = mapped_column(Float, default=0.0)
    popularity_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Explanation payload
    # {"reasons": ["You liked Inception", "Similar director"], "confidence": 0.94}
    explanation: Mapped[dict] = mapped_column(JSONB, default=dict)

    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="recommendations")  # noqa: F821
    movie: Mapped["Movie"] = relationship("Movie", lazy="noload")
    feedback: Mapped[list["RecommendationFeedback"]] = relationship(
        "RecommendationFeedback", back_populates="recommendation", lazy="noload"
    )


# ── RecommendationFeedback ─────────────────────────────────────────────────────

class RecommendationFeedback(Base):
    """
    Records user actions on recommendations.
    Actions: 'liked', 'dismissed', 'clicked', 'watchlisted'
    Used by weight_updater.py to shift the hybrid ranker weights per user.
    """
    __tablename__ = "recommendation_feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    recommendation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # liked|dismissed|clicked|watchlisted
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    recommendation: Mapped["Recommendation"] = relationship("Recommendation", back_populates="feedback")
