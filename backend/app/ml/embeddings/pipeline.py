"""
app/ml/embeddings/pipeline.py
──────────────────────────────
Movie embedding pipeline.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.qdrant_client import (
    batch_upsert_movie_vectors,
)

from app.ml.embeddings.encoder import (
    build_movie_text,
    encode_texts,
)

from app.models.movie import Movie

logger = logging.getLogger(__name__)


# Quality filter thresholds
MIN_VOTE_COUNT = 100
MIN_VOTE_AVERAGE = 5.5
MIN_OVERVIEW_LENGTH = 40


def _movie_point_id(tmdb_id: int) -> int:
    """
    Qdrant point id helper.
    """
    return int(tmdb_id)


def is_high_quality_movie(movie: Movie) -> bool:
    """
    Prevent low-quality/noisy movies from entering vector space.
    """

    if (movie.vote_count or 0) < MIN_VOTE_COUNT:
        return False

    if (movie.vote_average or 0) < MIN_VOTE_AVERAGE:
        return False

    if not movie.overview:
        return False

    if len(movie.overview.strip()) < MIN_OVERVIEW_LENGTH:
        return False

    return True


async def embed_unprocessed_movies(
    db: AsyncSession,
    batch_size: int = 64,
    force_reembed: bool = False,
) -> int:
    """
    Generate embeddings and store them in Qdrant.
    """

    query = select(Movie)

    if not force_reembed:
        query = query.where(
            Movie.embedding_synced.is_(False)
        )

    result = await db.execute(query)

    all_movies = result.scalars().all()

    if not all_movies:

        logger.info(
            "No movies need embeddings"
        )

        return 0

    logger.info(
        f"Found {len(all_movies)} candidate movies"
    )

    # QUALITY FILTER
    movies = [
        movie
        for movie in all_movies
        if is_high_quality_movie(movie)
    ]

    filtered_out = len(all_movies) - len(movies)

    logger.info(
        f"Filtered out {filtered_out} low-quality movies"
    )

    logger.info(
        f"Embedding {len(movies)} high-quality movies"
    )

    embedded_count = 0

    for i in range(
        0,
        len(movies),
        batch_size,
    ):

        batch = movies[
            i : i + batch_size
        ]

        texts: list[str] = []

        for movie in batch:

            release_year = (
                movie.release_date.year
                if movie.release_date
                else None
            )

            text = build_movie_text({
                "title":
                    movie.title,

                "overview":
                    movie.overview,

                "genres":
                    movie.genres or [],

                "keywords":
                    movie.keywords or [],

                "mood_tags":
                    movie.mood_tags or [],

                "top_cast":
                    movie.top_cast or [],

                "director":
                    getattr(movie, "director", None),

                "release_date":
                    movie.release_date,

                "year":
                    release_year,
            })

            texts.append(text)

        embeddings = encode_texts(texts)

        qdrant_points = []

        for movie, vector in zip(
            batch,
            embeddings,
        ):

            release_year = (
                movie.release_date.year
                if movie.release_date
                else None
            )

            point_id = _movie_point_id(
                movie.tmdb_id
            )

            payload = {
                "tmdb_id":
                    int(movie.tmdb_id),

                "title":
                    movie.title,

                "genres":
                    movie.genres or [],

                "year":
                    release_year,

                "vote_average":
                    float(
                        movie.vote_average or 0
                    ),

                "popularity":
                    float(
                        movie.popularity or 0
                    ),

                "mood_tags":
                    movie.mood_tags or [],
            }

            qdrant_points.append(
                (
                    point_id,
                    vector.tolist(),
                    payload,
                )
            )

        await batch_upsert_movie_vectors(
            qdrant_points
        )

        for movie in batch:

            movie.embedding_synced = True

            movie.embedding_updated_at = (
                datetime.now(
                    timezone.utc
                )
            )

        await db.commit()

        embedded_count += len(batch)

        logger.info(
            f"Embedded batch "
            f"{embedded_count}/{len(movies)}"
        )

    logger.info(
        f"Embedding pipeline complete: "
        f"{embedded_count} movies embedded"
    )

    return embedded_count