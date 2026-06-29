"""
app/integrations/qdrant_client.py
──────────────────────────────────
Production-grade Qdrant integration for CineAI.

Features:
- semantic vector search
- advanced metadata filtering
- emotional retrieval
- mood-aware search
- year filtering
- vote filtering
- genre filtering
- ANN vector retrieval
- batch upserts
- user vectors
"""

import logging
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels

from app.config import settings

logger = logging.getLogger(__name__)

_qdrant: AsyncQdrantClient | None = None


# ─────────────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────────────

async def init_qdrant() -> None:

    global _qdrant

    _qdrant = AsyncQdrantClient(
        url=(
            f"http://"
            f"{settings.QDRANT_HOST}:"
            f"{settings.QDRANT_PORT}"
        ),

        api_key=(
            settings.QDRANT_API_KEY
            or None
        ),

        prefer_grpc=False,
    )

    await _ensure_collections()

    logger.info(
        "Qdrant initialised"
    )


async def close_qdrant() -> None:

    global _qdrant

    if _qdrant:

        await _qdrant.close()


def get_qdrant() -> AsyncQdrantClient:

    if _qdrant is None:

        raise RuntimeError(
            "Qdrant not initialised"
        )

    return _qdrant


# ─────────────────────────────────────────────────────
# COLLECTION SETUP
# ─────────────────────────────────────────────────────

async def _ensure_collections() -> None:

    client = get_qdrant()

    existing = {
        c.name
        for c in (
            await client.get_collections()
        ).collections
    }

    vector_params = qmodels.VectorParams(
        size=settings.VECTOR_DIMENSION,

        distance=qmodels.Distance.COSINE,
    )

    for name in [

        settings.QDRANT_COLLECTION_MOVIES,

        settings.QDRANT_COLLECTION_USERS,
    ]:

        if name not in existing:

            await client.create_collection(
                collection_name=name,

                vectors_config=vector_params,

                optimizers_config=(
                    qmodels.OptimizersConfigDiff(
                        indexing_threshold=20000,
                    )
                ),
            )

            logger.info(
                f"Created collection: "
                f"{name}"
            )


# ─────────────────────────────────────────────────────
# UPSERT
# ─────────────────────────────────────────────────────

async def upsert_movie_vector(
    point_id: str,
    vector: list[float],
    payload: dict[str, Any],
) -> None:

    client = get_qdrant()

    await client.upsert(
        collection_name=(
            settings.QDRANT_COLLECTION_MOVIES
        ),

        points=[
            qmodels.PointStruct(
                id=point_id,
                vector=vector,
                payload=payload,
            )
        ],
    )


async def upsert_user_vector(
    point_id: str,
    vector: list[float],
    payload: dict[str, Any],
) -> None:

    client = get_qdrant()

    await client.upsert(
        collection_name=(
            settings.QDRANT_COLLECTION_USERS
        ),

        points=[
            qmodels.PointStruct(
                id=point_id,
                vector=vector,
                payload=payload,
            )
        ],
    )


async def batch_upsert_movie_vectors(
    points: list[
        tuple[
            str,
            list[float],
            dict,
        ]
    ],

    batch_size: int = 100,
) -> None:

    client = get_qdrant()

    for i in range(
        0,
        len(points),
        batch_size,
    ):

        batch = points[
            i : i + batch_size
        ]

        await client.upsert(
            collection_name=(
                settings.QDRANT_COLLECTION_MOVIES
            ),

            points=[

                qmodels.PointStruct(
                    id=pid,
                    vector=vec,
                    payload=pl,
                )

                for pid, vec, pl in batch
            ],
        )

        logger.debug(
            f"Upserted batch "
            f"{i // batch_size + 1} "
            f"({len(batch)} points)"
        )


# ─────────────────────────────────────────────────────
# FILTER BUILDER
# ─────────────────────────────────────────────────────

def _build_search_filter(
    filters: dict | None,
) -> qmodels.Filter | None:

    if not filters:
        return None

    must_conditions = []

    # ─────────────────────────────
    # Genres
    # ─────────────────────────────

    genres = filters.get(
        "genres"
    )

    if genres:

        for genre in genres:

            must_conditions.append(
                qmodels.FieldCondition(
                    key="genres",

                    match=qmodels.MatchAny(
                        any=[genre]
                    ),
                )
            )

    # ─────────────────────────────
    # Mood tags
    # ─────────────────────────────

    mood_tags = filters.get(
        "mood_tags"
    )

    if mood_tags:

        for tag in mood_tags:

            must_conditions.append(
                qmodels.FieldCondition(
                    key="mood_tags",

                    match=qmodels.MatchAny(
                        any=[tag]
                    ),
                )
            )

    # ─────────────────────────────
    # Tone tags
    # ─────────────────────────────

    tone_tags = filters.get(
        "tone_tags"
    )

    if tone_tags:

        for tag in tone_tags:

            must_conditions.append(
                qmodels.FieldCondition(
                    key="tone_tags",

                    match=qmodels.MatchAny(
                        any=[tag]
                    ),
                )
            )

    # ─────────────────────────────
    # Year filtering
    # ─────────────────────────────

    min_year = filters.get(
        "min_year"
    )

    max_year = filters.get(
        "max_year"
    )

    if (
        min_year is not None
        or max_year is not None
    ):

        must_conditions.append(
            qmodels.FieldCondition(
                key="year",

                range=qmodels.Range(
                    gte=min_year,
                    lte=max_year,
                ),
            )
        )

    # ─────────────────────────────
    # Rating filtering
    # ─────────────────────────────

    min_vote = filters.get(
        "min_vote_average"
    )

    if min_vote is not None:

        must_conditions.append(
            qmodels.FieldCondition(
                key="vote_average",

                range=qmodels.Range(
                    gte=float(min_vote)
                ),
            )
        )

    # ─────────────────────────────
    # Popularity filtering
    # ─────────────────────────────

    min_popularity = filters.get(
        "min_popularity"
    )

    if min_popularity is not None:

        must_conditions.append(
            qmodels.FieldCondition(
                key="popularity",

                range=qmodels.Range(
                    gte=float(
                        min_popularity
                    )
                ),
            )
        )

    if not must_conditions:
        return None

    return qmodels.Filter(
        must=must_conditions
    )


# ─────────────────────────────────────────────────────
# SEARCH
# ─────────────────────────────────────────────────────

async def search_similar_movies(
    query_vector: list[float],

    top_k: int = 50,

    score_threshold: float = 0.08,

    filters: dict | None = None,
) -> list[dict[str, Any]]:
    """
    Advanced semantic movie retrieval.
    """

    client = get_qdrant()

    qdrant_filter = (
        _build_search_filter(
            filters
        )
    )

    results = await client.search(
        collection_name=(
            settings.QDRANT_COLLECTION_MOVIES
        ),

        query_vector=query_vector,

        limit=top_k,

        score_threshold=score_threshold,

        query_filter=qdrant_filter,

        with_payload=True,
    )

    logger.info(
        f"Semantic search returned "
        f"{len(results)} results "
        f"(threshold={score_threshold})"
    )

    parsed = []

    for hit in results:

        payload = hit.payload or {}

        parsed.append({

            "point_id":
                str(hit.id),

            "score":
                float(hit.score),

            "tmdb_id":
                payload.get("tmdb_id"),

            "title":
                payload.get("title"),

            "genres":
                payload.get(
                    "genres",
                    [],
                ),

            "year":
                payload.get("year"),

            "vote_average":
                payload.get(
                    "vote_average",
                    0,
                ),

            "popularity":
                payload.get(
                    "popularity",
                    0,
                ),

            "mood_tags":
                payload.get(
                    "mood_tags",
                    [],
                ),

            "tone_tags":
                payload.get(
                    "tone_tags",
                    [],
                ),

            "theme_tags":
                payload.get(
                    "theme_tags",
                    [],
                ),

            "pacing_tags":
                payload.get(
                    "pacing_tags",
                    [],
                ),

            "emotion_tags":
                payload.get(
                    "emotion_tags",
                    [],
                ),
        })

    return parsed


# ─────────────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────────────

async def delete_movie_vector(
    point_id: str,
) -> None:

    client = get_qdrant()

    await client.delete(
        collection_name=(
            settings.QDRANT_COLLECTION_MOVIES
        ),

        points_selector=(
            qmodels.PointIdsList(
                points=[point_id]
            )
        ),
    )


# ─────────────────────────────────────────────────────
# INFO
# ─────────────────────────────────────────────────────

async def get_collection_info() -> dict:

    client = get_qdrant()

    info = await client.get_collection(
        settings.QDRANT_COLLECTION_MOVIES
    )

    return {

        "vectors_count":
            info.vectors_count,

        "indexed_vectors_count":
            info.indexed_vectors_count,

        "status":
            info.status,
    }