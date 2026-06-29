"""
app/ml/recommenders/hybrid.py
───────────────────────────────
Hybrid recommendation engine.

Fusion formula:
  composite = α·semantic + β·content + γ·collaborative + δ·popularity_decay

Score calibration fixes:
  - Per-signal min-max normalization before blending
  - Semantic weight raised to 0.50
  - Collaborative weight lowered to 0.15
  - Popularity weight lowered to 0.05
  - Quality floor: vote_average >= 5.5
  - Composite score sigmoid stretch

Refresh diversity:
  - randomize=True adds small score noise to top candidate pool
  - surfaces different movies on each refresh without hurting quality
"""

import asyncio
import logging
import math
import random
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.ml.recommenders.base import BaseRecommender, MovieScore
from app.ml.recommenders.semantic import SemanticRecommender
from app.ml.recommenders.content_based import ContentBasedRecommender
from app.ml.recommenders.collaborative import get_collaborative_recommender
from app.models.movie import Movie

logger = logging.getLogger(__name__)

_QUALITY_FLOOR = 5.5
# Noise range for refresh diversity — small enough not to hurt quality
# large enough to surface different top-20 from the top-50 pool
_REFRESH_NOISE = 0.06


def _minmax_normalize(scores: dict[int, float]) -> dict[int, float]:
    if not scores:
        return {}
    values = list(scores.values())
    lo, hi = min(values), max(values)
    if hi == lo:
        return {k: 0.5 for k in scores}
    return {k: (v - lo) / (hi - lo) for k, v in scores.items()}


def _sigmoid_stretch(score: float) -> float:
    x = (score - 0.4) * 6
    return round(1 / (1 + math.exp(-x)), 4)


class HybridRanker:

    def __init__(
        self,
        semantic: SemanticRecommender,
        content: ContentBasedRecommender,
    ) -> None:
        self._semantic = semantic
        self._content = content
        self._collab = get_collaborative_recommender()

    async def rank(
        self,
        user_context: dict,
        db: AsyncSession,
        top_k: int = settings.RECOMMENDATION_TOP_K,
        diversity_factor: float = 0.15,
        randomize: bool = False,
    ) -> list[dict]:

        exclude_ids = set(user_context.get("rated_movie_ids", []))
        exclude_ids.update(user_context.get("watchlist_movie_ids", []))

        semantic_results, content_results, collab_results = await asyncio.gather(
            self._semantic.recommend(user_context, exclude_ids, top_k=settings.VECTOR_SEARCH_TOP_K),
            self._content.recommend(user_context, exclude_ids, top_k=settings.VECTOR_SEARCH_TOP_K),
            self._collab.recommend(user_context, exclude_ids, top_k=settings.VECTOR_SEARCH_TOP_K),
        )

        candidate_scores: dict[int, dict[str, float]] = defaultdict(
            lambda: {"semantic": 0.0, "content": 0.0, "collaborative": 0.0}
        )

        for ms in semantic_results:
            candidate_scores[ms.tmdb_id]["semantic"] = ms.score
        for ms in content_results:
            candidate_scores[ms.tmdb_id]["content"] = ms.score
        for ms in collab_results:
            candidate_scores[ms.tmdb_id]["collaborative"] = ms.score

        if not candidate_scores:
            logger.warning("All recommenders returned empty")
            return []

        candidate_ids = list(candidate_scores.keys())
        movies_result = await db.execute(
            select(Movie).where(Movie.tmdb_id.in_(candidate_ids))
        )
        movies: list[Movie] = list(movies_result.scalars().all())
        movie_map: dict[int, Movie] = {m.tmdb_id: m for m in movies}

        # Quality floor
        candidate_ids = [
            mid for mid in candidate_ids
            if mid in movie_map
            and (movie_map[mid].vote_average or 0) >= _QUALITY_FLOOR
        ]

        if not candidate_ids:
            logger.warning("All candidates filtered by quality floor")
            return []

        # Per-signal normalization
        norm_semantic = _minmax_normalize({mid: candidate_scores[mid]["semantic"] for mid in candidate_ids})
        norm_content = _minmax_normalize({mid: candidate_scores[mid]["content"] for mid in candidate_ids})
        norm_collab = _minmax_normalize({mid: candidate_scores[mid]["collaborative"] for mid in candidate_ids})
        norm_pop = _minmax_normalize({
            mid: (movie_map[mid].vote_average or 0) / 10.0
            for mid in candidate_ids
        })

        ab_group = user_context.get("ab_group", "control")
        
        if ab_group == "variant":
            weights = user_context.get("hybrid_weights") or {
                "semantic": 0.60,
                "content": 0.10,
                "collaborative": 0.20,
                "popularity": 0.10,
            }
        else:
            weights = user_context.get("hybrid_weights") or {
                "semantic": settings.WEIGHT_SEMANTIC,
                "content": settings.WEIGHT_CONTENT,
                "collaborative": settings.WEIGHT_COLLABORATIVE,
                "popularity": settings.WEIGHT_POPULARITY,
            }

        ranked: list[dict] = []

        for tmdb_id in candidate_ids:
            sem = norm_semantic.get(tmdb_id, 0.0)
            con = norm_content.get(tmdb_id, 0.0)
            col = norm_collab.get(tmdb_id, 0.0)
            pop = norm_pop.get(tmdb_id, 0.0)

            raw_composite = (
                weights["semantic"] * sem
                + weights["content"] * con
                + weights["collaborative"] * col
                + weights["popularity"] * pop
            )

            composite = _sigmoid_stretch(raw_composite)

            ranked.append({
                "tmdb_id": tmdb_id,
                "composite_score": composite,
                "semantic_score": round(sem, 4),
                "content_score": round(con, 4),
                "collab_score": round(col, 4),
                "popularity_score": round(pop, 4),
                "movie": movie_map[tmdb_id],
            })

        ranked.sort(key=lambda x: x["composite_score"], reverse=True)

        # ── Refresh diversity ─────────────────────────────────────────────
        # Add small score noise to top candidate pool so refresh
        # surfaces different movies without hurting overall quality.
        # Only applied when randomize=True (force refresh path).
        if randomize:
            pool_size = min(len(ranked), top_k * 3)
            for item in ranked[:pool_size]:
                item["composite_score"] = round(
                    max(0.0, min(1.0, item["composite_score"] + random.uniform(-_REFRESH_NOISE, _REFRESH_NOISE))),
                    4,
                )
            ranked[:pool_size] = sorted(
                ranked[:pool_size],
                key=lambda x: x["composite_score"],
                reverse=True,
            )
            logger.info(f"[hybrid] refresh randomization applied pool_size={pool_size}")

        if diversity_factor > 0:
            ranked = _apply_diversity(ranked, diversity_factor)

        return ranked[:top_k]

    async def rank_similar(
        self,
        movie_id: int,
        db: AsyncSession,
        top_k: int = 20,
    ) -> list[dict]:

        content_results = self._content.get_similar_to_movie(
            movie_id=movie_id,
            top_k=top_k * 2,
            exclude_ids={movie_id},
        )

        if not content_results:
            return []

        candidate_ids = [ms.tmdb_id for ms in content_results]
        movies_result = await db.execute(
            select(Movie).where(Movie.tmdb_id.in_(candidate_ids))
        )
        movie_map = {m.tmdb_id: m for m in movies_result.scalars().all()}
        content_score_map = {ms.tmdb_id: ms.score for ms in content_results}

        ranked = []
        for tmdb_id in candidate_ids:
            if tmdb_id not in movie_map:
                continue
            ranked.append({
                "tmdb_id": tmdb_id,
                "composite_score": content_score_map.get(tmdb_id, 0.0),
                "semantic_score": 0.0,
                "content_score": content_score_map.get(tmdb_id, 0.0),
                "collab_score": 0.0,
                "popularity_score": 0.0,
                "movie": movie_map[tmdb_id],
                "shared_attributes": _get_shared_attributes(
                    movie_map.get(movie_id), movie_map[tmdb_id]
                ) if movie_id in movie_map else [],
            })

        ranked.sort(key=lambda x: x["composite_score"], reverse=True)
        return ranked[:top_k]


def _apply_diversity(ranked: list[dict], factor: float) -> list[dict]:
    if len(ranked) <= 1:
        return ranked

    seen_directors: set[str] = set()
    result = []

    for item in ranked:
        movie: Movie = item["movie"]
        director = movie.director
        penalty = factor if director and director in seen_directors else 0.0
        item["composite_score"] = round(item["composite_score"] * (1 - penalty), 4)
        if director:
            seen_directors.add(director)
        result.append(item)

    result.sort(key=lambda x: x["composite_score"], reverse=True)
    return result


def _get_shared_attributes(source: Movie | None, target: Movie) -> list[str]:
    if source is None:
        return []

    attrs = []

    if source.director and source.director == target.director:
        attrs.append(f"Directed by {source.director}")

    shared_genres = set(source.genres or []) & set(target.genres or [])
    for g in list(shared_genres)[:2]:
        attrs.append(g)

    shared_cast = set(source.top_cast) & set(target.top_cast)
    for actor in list(shared_cast)[:1]:
        attrs.append(f"Starring {actor}")

    shared_moods = set(source.mood_tags or []) & set(target.mood_tags or [])
    for mood in list(shared_moods)[:2]:
        attrs.append(mood.capitalize())

    return attrs[:4]