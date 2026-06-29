"""
app/api/v1/movies.py
──────────────────────
Movie endpoints:
  GET /movies/trending
  GET /movies/popular
  GET /movies/top-rated
  GET /movies/{id}
  GET /movies/{id}/similar

Performance fixes:
  - /popular and /top-rated now cached (TTL 30min)
  - similar movies cached (TTL 1hr)
  - trending/popular/top-rated use batch DB fetch instead of N sequential lookups
  - timing logs on all endpoints
"""

import logging
import time

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis_client import (
    cache_get,
    cache_set,
    movie_cache_key,
    trending_cache_key,
)
from app.integrations.tmdb_client import TMDbClient
from app.models.movie import Movie
from app.schemas import MovieCardResponse, MovieDetailResponse
from app.services.movie_service import MovieService
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/movies", tags=["Movies"])
logger = logging.getLogger(__name__)

_POPULAR_CACHE_TTL = 1800       # 30 min
_TOP_RATED_CACHE_TTL = 1800     # 30 min
_SIMILAR_CACHE_TTL = 3600       # 1 hr
_DETAIL_CACHE_TTL = 3600        # 1 hr


def _popular_cache_key(page: int) -> str:
    return f"popular:page:{page}"


def _top_rated_cache_key(page: int) -> str:
    return f"top_rated:page:{page}"


def _similar_cache_key(movie_id: int) -> str:
    return f"similar:{movie_id}"


async def _batch_fetch_cards(
    db: AsyncSession,
    service: MovieService,
    tmdb_items: list[dict],
) -> list[MovieCardResponse]:
    """
    FIX: batch fetch movies from DB in one query,
    then upsert only the missing ones individually.
    Was: N sequential get_or_fetch_movie() calls.
    Now: 1 DB query + only missing items fetched from TMDb.
    """
    tmdb_ids = [item["tmdb_id"] for item in tmdb_items]

    # Batch fetch all from DB
    result = await db.execute(
        select(Movie).where(Movie.tmdb_id.in_(tmdb_ids))
    )
    existing = {m.tmdb_id: m for m in result.scalars().all()}

    # Only fetch missing ones from TMDb
    missing_ids = [tid for tid in tmdb_ids if tid not in existing]
    for tmdb_id in missing_ids:
        try:
            movie = await service.get_or_fetch_movie(tmdb_id)
            existing[tmdb_id] = movie
        except Exception:
            continue

    # Return in original order
    cards = []
    for item in tmdb_items:
        movie = existing.get(item["tmdb_id"])
        if movie:
            cards.append(MovieService.to_card(movie))
    return cards


# ─────────────────────────────────────────────────────
# TRENDING
# ─────────────────────────────────────────────────────

@router.get("/trending", response_model=list[MovieCardResponse])
async def get_trending(
    page: int = Query(1, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
):
    t0 = time.perf_counter()
    cache_key = trending_cache_key(page)

    cached = await cache_get(cache_key)
    if cached:
        logger.info(f"[movies] trending cache HIT page={page} t={time.perf_counter()-t0:.3f}s")
        return [MovieCardResponse(**m) for m in cached]

    service = MovieService(db, TMDbClient())
    async with TMDbClient() as client:
        data = await client.get_trending(page=page)

    movies = await _batch_fetch_cards(db, service, data["results"])

    await cache_set(cache_key, [m.model_dump(mode="json") for m in movies], ttl=1800)
    logger.info(f"[movies] trending page={page} results={len(movies)} t={time.perf_counter()-t0:.3f}s")
    return movies


# ─────────────────────────────────────────────────────
# POPULAR
# ─────────────────────────────────────────────────────

@router.get("/popular", response_model=list[MovieCardResponse])
async def get_popular(
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
):
    t0 = time.perf_counter()

    # FIX: was not cached at all
    cache_key = _popular_cache_key(page)
    cached = await cache_get(cache_key)
    if cached:
        logger.info(f"[movies] popular cache HIT page={page} t={time.perf_counter()-t0:.3f}s")
        return [MovieCardResponse(**m) for m in cached]

    service = MovieService(db, TMDbClient())
    async with TMDbClient() as client:
        data = await client.get_popular(page=page)

    movies = await _batch_fetch_cards(db, service, data["results"])

    await cache_set(cache_key, [m.model_dump(mode="json") for m in movies], ttl=_POPULAR_CACHE_TTL)
    logger.info(f"[movies] popular page={page} results={len(movies)} t={time.perf_counter()-t0:.3f}s")
    return movies


# ─────────────────────────────────────────────────────
# TOP RATED
# ─────────────────────────────────────────────────────

@router.get("/top-rated", response_model=list[MovieCardResponse])
async def get_top_rated(
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
):
    t0 = time.perf_counter()

    # FIX: was not cached at all
    cache_key = _top_rated_cache_key(page)
    cached = await cache_get(cache_key)
    if cached:
        logger.info(f"[movies] top_rated cache HIT page={page} t={time.perf_counter()-t0:.3f}s")
        return [MovieCardResponse(**m) for m in cached]

    service = MovieService(db, TMDbClient())
    async with TMDbClient() as client:
        data = await client.get_top_rated(page=page)

    movies = await _batch_fetch_cards(db, service, data["results"])

    await cache_set(cache_key, [m.model_dump(mode="json") for m in movies], ttl=_TOP_RATED_CACHE_TTL)
    logger.info(f"[movies] top_rated page={page} results={len(movies)} t={time.perf_counter()-t0:.3f}s")
    return movies


# ─────────────────────────────────────────────────────
# MOVIE DETAIL
# ─────────────────────────────────────────────────────

@router.get("/{movie_id}", response_model=MovieDetailResponse)
async def get_movie_detail(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
):
    t0 = time.perf_counter()
    cache_key = movie_cache_key(movie_id)

    cached = await cache_get(cache_key)
    if cached:
        logger.info(f"[movies] detail cache HIT id={movie_id} t={time.perf_counter()-t0:.3f}s")
        return MovieDetailResponse(**cached)

    service = MovieService(db, TMDbClient())
    movie = await service.get_or_fetch_movie(movie_id)
    detail = MovieService.to_detail(movie)

    await cache_set(cache_key, detail.model_dump(mode="json"), ttl=_DETAIL_CACHE_TTL)
    logger.info(f"[movies] detail id={movie_id} t={time.perf_counter()-t0:.3f}s")
    return detail


# ─────────────────────────────────────────────────────
# SIMILAR MOVIES
# ─────────────────────────────────────────────────────

@router.get("/{movie_id}/similar", response_model=list)
async def get_similar_movies(
    movie_id: int,
    top_k: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    t0 = time.perf_counter()

    # FIX: was not cached at all — runs full corpus + ranking every time
    cache_key = _similar_cache_key(movie_id)
    cached = await cache_get(cache_key)
    if cached:
        logger.info(f"[movies] similar cache HIT id={movie_id} t={time.perf_counter()-t0:.3f}s")
        return cached

    service = RecommendationService(db)
    results = await service.get_similar_movies(movie_id=movie_id, top_k=top_k)

    serialized = [r.model_dump(mode="json") for r in results]
    await cache_set(cache_key, serialized, ttl=_SIMILAR_CACHE_TTL)

    logger.info(f"[movies] similar id={movie_id} results={len(results)} t={time.perf_counter()-t0:.3f}s")
    return results