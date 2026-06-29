"""
app/workers/scheduler.py
──────────────────────────
APScheduler job definitions. Runs inside the FastAPI process.

Jobs:
  1. embed_new_movies     — Every 6 hours: embed/re-embed movies
  2. retrain_cf           — Every 24 hours (2am): rebuild CF ratings matrix
  3. refresh_trending     — Every 30 minutes: warm trending cache
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def start_scheduler() -> None:

    global _scheduler

    _scheduler = AsyncIOScheduler(timezone="UTC")

    # ── Embedding pipeline ────────────────────────────────────────────────
    _scheduler.add_job(
        _run_embedding_pipeline,
        trigger=IntervalTrigger(hours=6),
        id="embed_new_movies",
        name="Embed movies",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # ── Collaborative filtering rebuild ───────────────────────────────────
    # Replaces old SVD retrain job — no scikit-surprise needed
    _scheduler.add_job(
        _run_cf_training,
        trigger=CronTrigger(hour=2, minute=0),
        id="retrain_cf",
        name="Rebuild CF ratings matrix",
        replace_existing=True,
    )

    # ── Trending cache refresh ────────────────────────────────────────────
    _scheduler.add_job(
        _refresh_trending,
        trigger=IntervalTrigger(minutes=30),
        id="refresh_trending",
        name="Refresh trending cache",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("Background scheduler started")


def stop_scheduler() -> None:

    global _scheduler

    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Background scheduler stopped")


async def train_cf_on_startup() -> None:
    """
    Called once at app startup to initialize the CF model.
    Runs in background so it doesn't block server startup.
    """
    logger.info("Initializing CF model on startup")
    await _run_cf_training()


# ── Embedding pipeline ─────────────────────────────────────────────────────────

async def _run_embedding_pipeline() -> None:

    logger.info("Starting embedding pipeline job")

    try:
        from app.core.database import AsyncSessionLocal
        from app.ml.embeddings.pipeline import embed_unprocessed_movies

        async with AsyncSessionLocal() as db:
            count = await embed_unprocessed_movies(db, force_reembed=True)

        logger.info(f"Embedding pipeline complete: {count} movies embedded")

    except Exception as exc:
        logger.error(f"Embedding pipeline failed: {exc}")


# ── Collaborative filtering ────────────────────────────────────────────────────

async def _run_cf_training() -> None:
    """
    Rebuild the in-memory CF ratings matrix from current DB ratings.
    Fast (~1s for thousands of ratings) — safe to run at startup.
    """
    logger.info("Starting CF model rebuild")

    try:
        from app.core.database import AsyncSessionLocal
        from app.ml.recommenders.collaborative import get_collaborative_recommender

        async with AsyncSessionLocal() as db:
            cf = get_collaborative_recommender()
            metrics = await cf.train(db)

        logger.info(f"CF model rebuild complete: {metrics}")

    except Exception as exc:
        logger.error(f"CF model rebuild failed: {exc}")


# ── Trending cache refresh ─────────────────────────────────────────────────────

async def _refresh_trending() -> None:

    logger.info("Refreshing trending cache")

    try:
        from app.core.database import AsyncSessionLocal
        from app.core.redis_client import cache_set, trending_cache_key
        from app.integrations.tmdb_client import TMDbClient
        from app.services.movie_service import MovieService

        async with AsyncSessionLocal() as db:
            service = MovieService(db, TMDbClient())
            movies = await service.get_trending(page=1)
            cards = [MovieService.to_card(m) for m in movies]

            await cache_set(
                trending_cache_key(1),
                [c.model_dump(mode="json") for c in cards],
                ttl=1800,
            )

        logger.info("Trending cache refreshed")

    except Exception as exc:
        logger.error(f"Trending cache refresh failed: {exc}")