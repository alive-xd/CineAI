#!/usr/bin/env python3
"""
scripts/seed_movies.py
────────────────────────
Bulk seed the database with high-quality movies from TMDb,
then run the embedding pipeline to vectorise them.

Run from project root:
    cd backend && source .venv/bin/activate
    python ../scripts/seed_movies.py

Examples:
    python ../scripts/seed_movies.py --pages 10
    python ../scripts/seed_movies.py --pages 50
"""

import asyncio
import argparse
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.config import settings
from app.core.database import AsyncSessionLocal
from app.integrations.qdrant_client import init_qdrant
from app.integrations.tmdb_client import TMDbClient
from app.ml.embeddings.pipeline import embed_unprocessed_movies
from app.services.movie_service import MovieService


# Quality filter thresholds
MIN_VOTE_COUNT = 100
MIN_VOTE_AVERAGE = 5.5
MIN_OVERVIEW_LENGTH = 40


def is_high_quality_movie(movie_data: dict) -> bool:
    """
    Filter low-quality/noisy TMDb movies before insertion.
    """

    vote_count = movie_data.get("vote_count", 0)
    vote_average = movie_data.get("vote_average", 0)
    overview = movie_data.get("overview", "")

    if vote_count < MIN_VOTE_COUNT:
        return False

    if vote_average < MIN_VOTE_AVERAGE:
        return False

    if not overview:
        return False

    if len(overview.strip()) < MIN_OVERVIEW_LENGTH:
        return False

    return True


async def seed(pages: int = 20) -> None:
    print(f"\n🎬 CineAI Movie Seeder")
    print(f"   TMDb pages to fetch: {pages} (~{pages * 20 * 3} movies)")
    print(f"   Qdrant: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    print()

    # Init Qdrant collections
    await init_qdrant()

    async with AsyncSessionLocal() as db:
        service = MovieService(db, TMDbClient())

        # Fetch from multiple TMDb endpoints for diversity
        endpoints = [
            ("popular", lambda p: TMDbClient().get_popular(p)),
            ("top_rated", lambda p: TMDbClient().get_top_rated(p)),
            ("trending", lambda p: TMDbClient().get_trending(p, "week")),
        ]

        total_saved = 0
        filtered_out = 0
        failed = 0

        for endpoint_name, fetcher in endpoints:
            print(f"📥 Fetching from {endpoint_name}...")

            for page in range(1, pages + 1):
                try:
                    async with TMDbClient() as client:
                        if endpoint_name == "popular":
                            data = await client.get_popular(page)

                        elif endpoint_name == "top_rated":
                            data = await client.get_top_rated(page)

                        else:
                            data = await client.get_trending(page)

                    for item in data.get("results", []):
                        try:
                            async with TMDbClient() as client:
                                full_data = await client.get_movie(item["tmdb_id"])

                            # QUALITY FILTER
                            if not is_high_quality_movie(full_data):
                                filtered_out += 1
                                continue

                            await service._upsert_movie(full_data)
                            total_saved += 1

                        except Exception as e:
                            failed += 1
                            print(f"   Skip {item.get('tmdb_id')}: {e}")

                    print(
                        f"   Page {page}/{pages} "
                        f"| Saved: {total_saved} "
                        f"| Filtered: {filtered_out} "
                        f"| Failed: {failed}",
                        end="\r"
                    )

                    await asyncio.sleep(0.25)

                except Exception as e:
                    print(f"\n   Page {page} failed: {e}")
                    continue

            print()
            print(f"   ✓ Finished {endpoint_name}")

        print()
        print("🧠 Running embedding pipeline...")

        embedded = await embed_unprocessed_movies(db)

        print(f"   ✓ Embedded {embedded} movies into Qdrant")

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("✅ Seed Complete")
    print(f"   Saved:      {total_saved}")
    print(f"   Filtered:   {filtered_out}")
    print(f"   Failed:     {failed}")
    print(f"   Embedded:   {embedded}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed CineAI with TMDb movies")

    parser.add_argument(
        "--pages",
        type=int,
        default=20,
        help="TMDb pages per endpoint (20 movies each). Default: 20"
    )

    args = parser.parse_args()

    asyncio.run(seed(pages=args.pages))