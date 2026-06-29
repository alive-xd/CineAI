#!/usr/bin/env python3

"""
scripts/embed_movies.py
────────────────────────
Rebuild movie embeddings into Qdrant.
"""

import asyncio
import os
import sys

# Add backend to Python path
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "backend",
    ),
)

from app.core.database import AsyncSessionLocal

from app.integrations.qdrant_client import (
    init_qdrant,
)

from app.ml.embeddings.pipeline import (
    embed_unprocessed_movies,
)


async def main():

    print("\n🧠 CineAI Embedding Pipeline")
    print()

    await init_qdrant()

    async with AsyncSessionLocal() as db:

        count = await embed_unprocessed_movies(
            db=db,
            force_reembed=True,
        )

        print()
        print(
            f"✅ Embedded movies: {count}"
        )
        print()


if __name__ == "__main__":
    asyncio.run(main())