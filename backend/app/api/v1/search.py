"""
app/api/v1/search.py
──────────────────────
Semantic + keyword search endpoints.

Performance fixes:
  - Semantic search results cached in Redis (TTL 10min)
  - Timing logs for all slow operations
  - Cache key built from query + top_k + filters hash
"""

import hashlib
import json
import logging
import time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis_client import cache_get, cache_set, search_cache_key
from app.dependencies import get_optional_user
from app.integrations.tmdb_client import TMDbClient
from app.ml.embeddings.encoder import encode_single
from app.ml.recommenders.semantic import SemanticRecommender, detect_intent
from app.models.movie import Movie
from app.models.user import User
from app.schemas import (
    MovieCardResponse,
    MovieSearchFilters,
    SemanticSearchRequest,
)
from app.services.movie_service import MovieService

router = APIRouter(prefix="/search", tags=["Search"])

logger = logging.getLogger(__name__)

_SEARCH_CACHE_TTL = 600


# ─────────────────────────────────────────────────────
# KEYWORD SEARCH
# ─────────────────────────────────────────────────────

@router.get("", response_model=list[MovieCardResponse])
async def keyword_search(
    q: str = Query(min_length=1, max_length=200),
    page: int = Query(1, ge=1),
    genre: list[str] | None = Query(None),
    year_min: int | None = Query(None),
    year_max: int | None = Query(None),
    rating_min: float | None = Query(None, ge=0, le=10),
    language: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    t0 = time.perf_counter()

    filters = MovieSearchFilters(
        genres=genre,
        year_min=year_min,
        year_max=year_max,
        rating_min=rating_min,
        language=language,
        page=page,
    )

    service = MovieService(db, TMDbClient())
    movies = await service.search_keyword(q, filters)
    result = [MovieService.to_card(m) for m in movies]

    logger.info(f"[search] keyword q={q!r} results={len(result)} t={time.perf_counter()-t0:.3f}s")
    return result


# ─────────────────────────────────────────────────────
# SEMANTIC SEARCH
# ─────────────────────────────────────────────────────

@router.post("/semantic", response_model=list[MovieCardResponse])
async def semantic_search(
    body: SemanticSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    t0 = time.perf_counter()

    # FIX: include top_k in cache key so load more
    # gets its own cache entry instead of hitting the top_k=20 cache
    filters_hash = _hash_filters(body.filters, body.top_k)
    cache_key = search_cache_key(body.query, filters_hash)

    cached = await cache_get(cache_key)
    if cached:
        logger.info(
            f"[search] semantic cache HIT q={body.query!r} top_k={body.top_k} "
            f"t={time.perf_counter()-t0:.3f}s"
        )
        return [MovieCardResponse(**r) for r in cached]

    # ── Encode query ──────────────────────────────────
    t_enc = time.perf_counter()
    query_vector = encode_single(body.query)
    logger.info(f"[search] encode t={time.perf_counter()-t_enc:.3f}s")

    # ── Intent detection ──────────────────────────────
    intent = detect_intent(body.query)
    fetch_multiplier = 5 if intent == "similar_to" else 3
    fetch_k = max(body.top_k * fetch_multiplier, 50)

    qdrant_filter = _build_qdrant_filter(body.filters)

    # ── Qdrant search ─────────────────────────────────
    t_qdrant = time.perf_counter()
    searcher = SemanticRecommender()
    results = await searcher.search(
        query=body.query,
        query_vector=query_vector,
        top_k=fetch_k,
        filters=qdrant_filter,
    )
    logger.info(
        f"[search] qdrant hits={len(results)} "
        f"t={time.perf_counter()-t_qdrant:.3f}s"
    )

    if not results:
        return []

    # ── DB fetch ──────────────────────────────────────
    t_db = time.perf_counter()
    result_ids = []
    for r in results:
        try:
            result_ids.append(int(r.tmdb_id))
        except Exception:
            continue

    db_result = await db.execute(
        select(Movie).where(Movie.tmdb_id.in_(result_ids))
    )
    movies = list(db_result.scalars().all())
    movies_map = {int(m.tmdb_id): m for m in movies}
    logger.info(f"[search] db fetch t={time.perf_counter()-t_db:.3f}s")

    # ── Preserve ranked order ─────────────────────────
    final_movies = []
    for r in results:
        try:
            tmdb_id = int(r.tmdb_id)
        except Exception:
            continue
        movie = movies_map.get(tmdb_id)
        if movie:
            final_movies.append(movie)

    final_movies = final_movies[: body.top_k]
    response = [MovieService.to_card(m) for m in final_movies]

    await cache_set(
        cache_key,
        [r.model_dump(mode="json") for r in response],
        ttl=_SEARCH_CACHE_TTL,
    )

    logger.info(
        f"[search] semantic DONE q={body.query!r} top_k={body.top_k} intent={intent} "
        f"results={len(response)} total_t={time.perf_counter()-t0:.3f}s"
    )

    return response


# ─────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────

def _hash_filters(filters: MovieSearchFilters | None, top_k: int = 20) -> str:
    payload = {
        "top_k": top_k,
        "filters": filters.model_dump() if filters else None,
    }
    return hashlib.md5(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()[:12]


def _build_qdrant_filter(
    filters: MovieSearchFilters | None,
) -> dict | None:

    if not filters:
        return None

    conditions = []

    if filters.genres:
        conditions.append({
            "key": "genres",
            "match": {"any": filters.genres},
        })

    if filters.rating_min:
        conditions.append({
            "key": "vote_average",
            "range": {"gte": filters.rating_min},
        })

    if filters.year_min:
        conditions.append({
            "key": "year",
            "range": {"gte": filters.year_min},
        })

    if filters.year_max:
        conditions.append({
            "key": "year",
            "range": {"lte": filters.year_max},
        })

    if not conditions:
        return None

    return {"must": conditions}