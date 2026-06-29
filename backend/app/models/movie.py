"""
app/models/movie.py
────────────────────
Movies table. Mirrors TMDb data locally.

Design decisions:
  - genres, cast, and keywords stored as JSON strings to avoid N+1 join tables
    at this scale. Would normalise at 10M+ movies.
  - mood_tags is our computed field — derived during embedding pipeline from
    genre + overview analysis, stored for fast filter-based retrieval.
  - popularity_score is a decayed version of TMDb's score, recomputed nightly.
"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Movie(Base):
    __tablename__ = "movies"

    # TMDb's integer ID as our primary key — natural key, no UUID needed
    tmdb_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    title: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        index=True,
    )

    original_title: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    overview: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    tagline: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )

    # ── Metadata ───────────────────────────────────────────────────────────────
    release_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        index=True,
    )

    runtime: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    original_language: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # ── Scores ─────────────────────────────────────────────────────────────────
    vote_average: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        index=True,
    )

    vote_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    popularity: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        index=True,
    )

    # Computed nightly:
    # popularity_score = vote_avg * log(vote_count) * recency_decay
    popularity_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        index=True,
    )

    # ── Images ─────────────────────────────────────────────────────────────────
    poster_path: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    backdrop_path: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # ── Structured arrays stored as JSONB ─────────────────────────────────────

    # Example: ["Action", "Sci-Fi"]
    genres: Mapped[list] = mapped_column(
        JSONB,
        default=list,
    )

    # Example:
    # [{"id": 1, "name": "Christopher Nolan", "job": "Director"}]
    crew: Mapped[list] = mapped_column(
        JSONB,
        default=list,
    )

    # Example:
    # [{"id": 1, "name": "Leonardo DiCaprio", "character": "Dom"}]
    cast: Mapped[list] = mapped_column(
        JSONB,
        default=list,
    )

    # Example:
    # ["mindbending", "philosophical", "epic", "dark"]
    mood_tags: Mapped[list] = mapped_column(
        JSONB,
        default=list,
    )

    # Emotional tone tags
    # Example:
    # ["dark", "melancholic", "hopeful"]
    tone_tags: Mapped[list] = mapped_column(
        JSONB,
        default=list,
    )

    # Narrative themes
    # Example:
    # ["grief", "identity", "survival"]
    theme_tags: Mapped[list] = mapped_column(
        JSONB,
        default=list,
    )

    # Viewing pace/style
    # Example:
    # ["slow-burn", "fast-paced"]
    pacing_tags: Mapped[list] = mapped_column(
        JSONB,
        default=list,
    )

    # Emotional impact
    # Example:
    # ["heartbreaking", "tense", "uplifting"]
    emotion_tags: Mapped[list] = mapped_column(
        JSONB,
        default=list,
    )

    # TMDb keyword strings
    keywords: Mapped[list] = mapped_column(
        JSONB,
        default=list,
    )

    # Production companies
    production_companies: Mapped[list] = mapped_column(
        JSONB,
        default=list,
    )

    # ── Sync tracking ──────────────────────────────────────────────────────────
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    embedding_synced: Mapped[bool] = mapped_column(
        default=False,
    )

    embedding_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    ratings: Mapped[list["Rating"]] = relationship(  # noqa: F821
        "Rating",
        back_populates="movie",
        lazy="noload",
    )

    watchlist_entries: Mapped[list["Watchlist"]] = relationship(  # noqa: F821
        "Watchlist",
        back_populates="movie",
        lazy="noload",
    )

    reviews: Mapped[list["Review"]] = relationship(  # noqa: F821
        "Review",
        back_populates="movie",
        lazy="noload",
    )

    embedding: Mapped["MovieEmbedding | None"] = relationship(  # noqa: F821
        "MovieEmbedding",
        back_populates="movie",
        uselist=False,
        lazy="noload",
    )

    # ── Helpers ────────────────────────────────────────────────────────────────
    @property
    def director(self) -> str | None:

        for member in self.crew:

            if member.get("job") == "Director":
                return member.get("name")

        return None

    @property
    def top_cast(self) -> list[str]:

        return [
            c["name"]
            for c in self.cast[:5]
        ]

    @property
    def poster_url(self) -> str | None:

        if self.poster_path:
            return (
                "https://image.tmdb.org/t/p/w500"
                f"{self.poster_path}"
            )

        return None

    @property
    def backdrop_url(self) -> str | None:

        if self.backdrop_path:
            return (
                "https://image.tmdb.org/t/p/original"
                f"{self.backdrop_path}"
            )

        return None

    @property
    def year(self) -> int | None:

        return (
            self.release_date.year
            if self.release_date
            else None
        )

    def __repr__(self) -> str:

        return (
            f"<Movie "
            f"id={self.tmdb_id} "
            f"title={self.title!r}>"
        )