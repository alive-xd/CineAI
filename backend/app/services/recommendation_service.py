"""
app/services/recommendation_service.py
─────────────────────────────────────────
Orchestrates the full recommendation pipeline for a user.

Performance fixes:
  - _build_user_context: 4 sequential DB queries → asyncio.gather (parallel)
  - _get_corpus: per-request in-memory cache → Redis cache (TTL 1hr)
  - _persist_recommendations: blocking response → fire-and-forget background task
  - Timing logs throughout pipeline
"""

import asyncio
import logging
import time
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import (
    cache_delete,
    cache_get,
    cache_set,
    rec_cache_key,
)

from app.ml.explainability.explainer import (
    explain_recommendation,
    explain_similar_movie,
)

from app.ml.recommenders.content_based import ContentBasedRecommender
from app.ml.recommenders.hybrid import HybridRanker
from app.ml.recommenders.semantic import SemanticRecommender

from app.models.all_models import (
    Rating,
    Recommendation,
    UserPreference,
    Watchlist,
)

from app.models.movie import Movie

from app.schemas import (
    RecommendationResponse,
    ScoreBreakdown,
    SimilarMovieResponse,
)

from app.services.movie_service import MovieService

logger = logging.getLogger(__name__)

# Corpus cache key + TTL
_CORPUS_CACHE_KEY = "corpus:movies:v1"
_CORPUS_CACHE_TTL = 3600  # 1 hour


class RecommendationService:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ─────────────────────────────────────────────────────────────────────
    # Recommendations
    # ─────────────────────────────────────────────────────────────────────

    async def get_recommendations(
        self,
        user_id: str,
        top_k: int = 20,
        force_refresh: bool = False,
    ) -> list[RecommendationResponse]:

        t0 = time.perf_counter()
        cache_key = rec_cache_key(user_id)

        if not force_refresh:
            cached = await cache_get(cache_key)
            if cached:
                logger.info(
                    f"[recs] cache HIT user={user_id} "
                    f"t={time.perf_counter()-t0:.3f}s"
                )
                return [RecommendationResponse(**r) for r in cached]

        # ── User context (parallel DB queries) ───────────────────────────
        t_ctx = time.perf_counter()
        user_context = await self._build_user_context(user_id)
        logger.info(f"[recs] user_context t={time.perf_counter()-t_ctx:.3f}s")

        if user_context["total_ratings"] < 5:
            logger.info(f"[recs] cold start user={user_id}")
            return []

        # ── Corpus (Redis-cached) ─────────────────────────────────────────
        t_corpus = time.perf_counter()
        corpus = await self._get_corpus()
        logger.info(f"[recs] corpus size={len(corpus)} t={time.perf_counter()-t_corpus:.3f}s")

        # ── Hybrid ranking ────────────────────────────────────────────────
        t_rank = time.perf_counter()
        semantic = SemanticRecommender()
        content = ContentBasedRecommender(corpus)
        ranker = HybridRanker(semantic=semantic, content=content)

        ranked = await ranker.rank(
            user_context=user_context,
            db=self.db,
            top_k=top_k,
            randomize=force_refresh,
        )
        logger.info(
            f"[recs] ranking results={len(ranked)} "
            f"t={time.perf_counter()-t_rank:.3f}s"
        )

        if not ranked:
            logger.warning(f"[recs] no results for user={user_id}")
            return []

        # ── Build responses ───────────────────────────────────────────────
        responses: list[RecommendationResponse] = []
        db_recs: list[dict] = []

        for item in ranked:
            movie: Movie = item["movie"]
            scores = {
                "semantic": item["semantic_score"],
                "content": item["content_score"],
                "collaborative": item["collab_score"],
                "popularity": item["popularity_score"],
                "composite": item["composite_score"],
            }
            explanation = explain_recommendation(movie, scores, user_context)

            db_recs.append({
                "user_id": user_id,
                "movie_id": movie.tmdb_id,
                "score": item["composite_score"],
                "semantic_score": item["semantic_score"],
                "content_score": item["content_score"],
                "collab_score": item["collab_score"],
                "popularity_score": item["popularity_score"],
                "explanation": explanation,
            })

            responses.append(RecommendationResponse(
                recommendation_id=str(uuid4()),
                movie=MovieService.to_card(movie),
                score=ScoreBreakdown(
                    semantic=item["semantic_score"],
                    content=item["content_score"],
                    collaborative=item["collab_score"],
                    popularity=item["popularity_score"],
                    composite=item["composite_score"],
                ),
                reasons=explanation["reasons"],
                confidence=explanation["confidence"],
                match_label=explanation["match_label"],
            ))

        # ── Cache responses ───────────────────────────────────────────────
        await cache_set(
            cache_key,
            [r.model_dump(mode="json") for r in responses],
        )

        # ── Persist to DB (fire-and-forget) ───────────────────────────────
        # FIX: don't block the response waiting for DB writes
        asyncio.create_task(
            self._persist_recommendations_safe(user_id=user_id, recs=db_recs)
        )

        logger.info(
            f"[recs] DONE user={user_id} results={len(responses)} "
            f"total_t={time.perf_counter()-t0:.3f}s"
        )

        return responses

    # ─────────────────────────────────────────────────────────────────────
    # Similar movies
    # ─────────────────────────────────────────────────────────────────────

    async def get_similar_movies(
        self,
        movie_id: int,
        top_k: int = 20,
    ) -> list[SimilarMovieResponse]:

        corpus = await self._get_corpus()
        content = ContentBasedRecommender(corpus)

        similar_ranked = await HybridRanker(
            semantic=SemanticRecommender(),
            content=content,
        ).rank_similar(movie_id=movie_id, db=self.db, top_k=top_k)

        source_result = await self.db.execute(
            select(Movie).where(Movie.tmdb_id == movie_id)
        )
        source_movie = source_result.scalar_one_or_none()

        responses = []
        for item in similar_ranked:
            movie: Movie = item["movie"]
            shared = item.get("shared_attributes", [])
            explanation = explain_similar_movie(
                source_movie, movie, item["composite_score"], shared
            )
            responses.append(SimilarMovieResponse(
                movie=MovieService.to_card(movie),
                similarity_score=item["composite_score"],
                shared_attributes=explanation["reasons"],
            ))

        return responses

    # ─────────────────────────────────────────────────────────────────────
    # Cache
    # ─────────────────────────────────────────────────────────────────────

    async def invalidate_cache(self, user_id: str) -> None:
        await cache_delete(rec_cache_key(user_id))

    # ─────────────────────────────────────────────────────────────────────
    # User context — FIX: parallel DB queries
    # ─────────────────────────────────────────────────────────────────────

    async def _build_user_context(self, user_id: str) -> dict:

        # FIX: was 4 sequential awaits, now parallel
        from app.models.user import User
        pref_result, ratings_result, wl_result, user_result = await asyncio.gather(
            self.db.execute(
                select(UserPreference).where(UserPreference.user_id == user_id)
            ),
            self.db.execute(
                select(Rating).where(Rating.user_id == user_id)
            ),
            self.db.execute(
                select(Watchlist).where(Watchlist.user_id == user_id)
            ),
            self.db.execute(
                select(User).where(User.id == user_id)
            ),
        )

        pref = pref_result.scalar_one_or_none()
        ratings = ratings_result.scalars().all()
        watchlist = wl_result.scalars().all()
        user = user_result.scalar_one_or_none()

        top_rated = sorted(ratings, key=lambda r: r.score, reverse=True)[:5]

        liked_titles = []
        liked_movie_genres: dict[str, list[str]] = {}

        if top_rated:
            movie_result = await self.db.execute(
                select(Movie.title, Movie.genres).where(
                    Movie.tmdb_id.in_([r.movie_id for r in top_rated])
                )
            )
            rows = movie_result.fetchall()
            liked_titles = [row[0] for row in rows]
            liked_movie_genres = {row[0]: row[1] or [] for row in rows}

        return {
            "user_id": user_id,
            "ab_group": user.ab_group if user else "control",
            "embedding_centroid": pref.embedding_centroid if pref else None,
            "genre_weights": pref.genre_weights if pref else {},
            "director_affinities": pref.director_affinities if pref else {},
            "mood_tag_weights": pref.mood_tag_weights if pref else {},
            "hybrid_weights": pref.hybrid_weights if pref else None,
            "total_ratings": len(ratings),
            "rated_movies": [
                {"movie_id": r.movie_id, "score": r.score} for r in ratings
            ],
            "rated_movie_ids": [r.movie_id for r in ratings],
            "watchlist_movie_ids": [w.movie_id for w in watchlist],
            "liked_movie_titles": liked_titles,
            "liked_movie_genres": liked_movie_genres,
        }

    # ─────────────────────────────────────────────────────────────────────
    # Corpus — FIX: Redis cache instead of per-request in-memory
    # ─────────────────────────────────────────────────────────────────────

    async def _get_corpus(self) -> list[dict]:
        # Check Redis first
        cached = await cache_get(_CORPUS_CACHE_KEY)
        if cached:
            return cached

        # Fetch from DB and cache
        svc = MovieService(self.db, None)
        corpus = await svc.get_movies_for_corpus(limit=5000)

        await cache_set(_CORPUS_CACHE_KEY, corpus, ttl=_CORPUS_CACHE_TTL)
        logger.info(f"[recs] corpus cached in Redis ({len(corpus)} movies)")

        return corpus

    # ─────────────────────────────────────────────────────────────────────
    # Persistence — FIX: safe wrapper for fire-and-forget
    # ─────────────────────────────────────────────────────────────────────

    async def _persist_recommendations_safe(
        self,
        user_id: str,
        recs: list[dict],
    ) -> None:
        """
        Fire-and-forget wrapper — errors logged but never
        bubble up to the user response.
        """
        try:
            await self._persist_recommendations(user_id=user_id, recs=recs)
        except Exception:
            logger.exception(f"[recs] background persist failed user={user_id}")

    async def _persist_recommendations(
        self,
        user_id: str,
        recs: list[dict],
    ) -> None:

        try:
            await self.db.execute(
                delete(Recommendation).where(Recommendation.user_id == user_id)
            )
            await self.db.flush()

            self.db.add_all([
                Recommendation(
                    id=uuid4(),
                    user_id=rec["user_id"],
                    movie_id=rec["movie_id"],
                    score=rec["score"],
                    semantic_score=rec["semantic_score"],
                    content_score=rec["content_score"],
                    collab_score=rec["collab_score"],
                    popularity_score=rec["popularity_score"],
                    explanation=rec["explanation"],
                )
                for rec in recs
            ])

            await self.db.commit()

        except Exception:
            await self.db.rollback()
            logger.exception(
                f"[recs] persist failed user={user_id}"
            )
            raise