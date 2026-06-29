"""
app/ml/embeddings/user_profile.py
────────────────────────────────────
Advanced user taste intelligence engine.

Features:
  - Weighted user taste embeddings
  - Strong-like amplification
  - Dislike penalties
  - Exponential recency decay
  - Taste clustering (multi-centroid)
  - Genre affinity modeling
  - Director affinity modeling
  - Mood preference modeling
  - Qdrant ANN user vectors
"""

import logging
from collections import defaultdict

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.integrations.qdrant_client import get_qdrant, upsert_user_vector
from app.ml.embeddings.pipeline import _movie_point_id
from app.models.all_models import Rating, UserPreference
from app.models.movie import Movie

logger = logging.getLogger(__name__)

# Minimum ratings needed to attempt clustering
_CLUSTER_MIN_RATINGS = 12
# Max clusters to try
_CLUSTER_MAX_K = 4
# Exponential decay half-life in days
# rating from 180 days ago = half the weight of today's rating
_RECENCY_HALF_LIFE_DAYS = 180


async def update_user_profile(
    user_id: str,
    db: AsyncSession,
) -> UserPreference | None:

    result = await db.execute(
        select(Rating, Movie)
        .join(Movie, Rating.movie_id == Movie.tmdb_id)
        .where(Rating.user_id == user_id)
        .order_by(Rating.created_at.desc())
    )

    rows = result.all()

    if not rows:
        return None

    ratings = [row[0] for row in rows]
    movies = [row[1] for row in rows]

    # Compute centroid (clustering-aware)
    centroid = await _compute_embedding_centroid(movies, ratings)

    # Compute affinity profiles
    genre_weights = _compute_genre_weights(movies, ratings)
    director_affinities = _compute_director_affinities(movies, ratings)
    mood_weights = _compute_mood_weights(movies, ratings)

    # Persist
    pref_result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    pref = pref_result.scalar_one_or_none()

    if pref is None:
        pref = UserPreference(user_id=user_id)
        db.add(pref)

    pref.embedding_centroid = centroid.tolist() if centroid is not None else None
    pref.genre_weights = genre_weights
    pref.director_affinities = director_affinities
    pref.mood_tag_weights = mood_weights
    pref.total_ratings = len(ratings)

    await db.commit()
    await db.refresh(pref)

    if centroid is not None:
        await upsert_user_vector(
            point_id=str(user_id).replace("-", ""),
            vector=centroid.tolist(),
            payload={
                "user_id": str(user_id),
                "top_genres": list(genre_weights.keys())[:5],
                "total_ratings": len(ratings),
            },
        )

    logger.info(
        f"Updated taste profile for user {user_id} ({len(ratings)} ratings)"
    )

    return pref


async def _compute_embedding_centroid(
    movies: list[Movie],
    ratings: list[Rating],
) -> np.ndarray | None:

    client = get_qdrant()

    point_ids = [_movie_point_id(m.tmdb_id) for m in movies]

    results = await client.retrieve(
        collection_name=settings.QDRANT_COLLECTION_MOVIES,
        ids=point_ids,
        with_vectors=True,
    )

    if not results:
        return None

    id_to_vector = {
        int(r.id): np.array(r.vector, dtype=np.float32)
        for r in results
    }

    # ── Collect weighted vectors ───────────────────────────
    now_ts = max(r.created_at.timestamp() for r in ratings)
    half_life_seconds = _RECENCY_HALF_LIFE_DAYS * 86400

    positive_vectors: list[np.ndarray] = []
    positive_weights: list[float] = []
    negative_vectors: list[np.ndarray] = []
    negative_weights: list[float] = []

    for movie, rating in zip(movies, ratings):
        pid = _movie_point_id(movie.tmdb_id)
        if pid not in id_to_vector:
            continue

        vector = id_to_vector[pid]
        score = float(rating.score)

        # ── Rating strength weight ─────────────────────────
        if score >= 4.5:
            base_weight = 2.5
        elif score >= 4.0:
            base_weight = 1.8
        elif score >= 3.0:
            base_weight = 1.0
        elif score >= 2.0:
            base_weight = 0.3
        else:
            base_weight = 1.5  # magnitude for negative vector

        # ── Exponential recency decay ──────────────────────
        # FIX: was linear (0.7 + ratio*0.8), now exponential
        # half-life = 180 days → old ratings fade much faster
        age_seconds = now_ts - rating.created_at.timestamp()
        recency_weight = 2 ** (-age_seconds / half_life_seconds)

        # ── Popularity dampening ───────────────────────────
        popularity_penalty = 0.85 if (movie.vote_count and movie.vote_count > 5000) else 1.0

        final_weight = base_weight * recency_weight * popularity_penalty

        if score < 2.0:
            # Negative signal — collect separately
            negative_vectors.append(vector * final_weight)
            negative_weights.append(final_weight)
        else:
            positive_vectors.append(vector * final_weight)
            positive_weights.append(final_weight)

    if not positive_vectors:
        return None

    # ── Taste clustering ───────────────────────────────────
    # If enough positive ratings, detect taste clusters
    # and blend their centroids weighted by cluster size.
    # This prevents horror + romcom averaging into nothing.
    if len(positive_vectors) >= _CLUSTER_MIN_RATINGS:
        centroid = _clustered_centroid(
            positive_vectors,
            positive_weights,
        )
    else:
        centroid = (
            np.sum(positive_vectors, axis=0)
            / max(sum(positive_weights), 1e-6)
        )

    # ── Subtract negative signals ──────────────────────────
    if negative_vectors:
        negative_centroid = (
            np.sum(negative_vectors, axis=0)
            / max(sum(negative_weights), 1e-6)
        )
        # Subtract 30% of negative centroid
        centroid = centroid - 0.30 * negative_centroid

    # L2 normalize
    norm = np.linalg.norm(centroid)
    if norm > 0:
        centroid = centroid / norm

    return centroid.astype(np.float32)


def _clustered_centroid(
    weighted_vectors: list[np.ndarray],
    weights: list[float],
) -> np.ndarray:
    """
    Detect taste clusters using k-means + silhouette score.
    Returns a weighted blend of per-cluster centroids.

    Example: user likes horror AND romcoms →
    two clusters, both represented in final centroid
    rather than averaging into an incoherent midpoint.
    """

    # Unweighted raw vectors for clustering
    raw = np.stack(weighted_vectors)

    best_k = 1
    best_score = -1.0

    # Try k=2..min(4, n//4) and pick best silhouette
    max_k = min(_CLUSTER_MAX_K, len(raw) // 4)

    for k in range(2, max_k + 1):
        try:
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = km.fit_predict(raw)
            score = silhouette_score(raw, labels)
            if score > best_score:
                best_score = score
                best_k = k
        except Exception:
            continue

    logger.info(f"Taste clustering: best_k={best_k} silhouette={best_score:.3f}")

    if best_k == 1:
        # No meaningful clusters — plain weighted average
        return np.sum(weighted_vectors, axis=0) / max(sum(weights), 1e-6)

    # Fit final k-means with best_k
    km = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    labels = km.fit_predict(raw)

    # Build weighted centroid per cluster
    cluster_centroids = []
    cluster_sizes = []

    for k in range(best_k):
        mask = labels == k
        if not mask.any():
            continue

        cluster_vecs = [
            weighted_vectors[i]
            for i in range(len(weighted_vectors)) if mask[i]
        ]
        cluster_ws = [
            weights[i]
            for i in range(len(weights)) if mask[i]
        ]

        cluster_centroid = (
            np.sum(cluster_vecs, axis=0)
            / max(sum(cluster_ws), 1e-6)
        )
        cluster_centroids.append(cluster_centroid)
        cluster_sizes.append(sum(cluster_ws))

    # Blend cluster centroids weighted by their total weight
    total_weight = sum(cluster_sizes)
    blended = sum(
        c * (s / total_weight)
        for c, s in zip(cluster_centroids, cluster_sizes)
    )

    return blended


def _compute_genre_weights(
    movies: list[Movie],
    ratings: list[Rating],
) -> dict[str, float]:

    genre_scores: dict[str, list[float]] = defaultdict(list)

    for movie, rating in zip(movies, ratings):
        normalised = (rating.score - 0.5) / 4.5
        for genre in (movie.genres or []):
            genre_scores[genre].append(normalised)

    weights = {
        genre: round(sum(scores) / len(scores), 3)
        for genre, scores in genre_scores.items()
        if len(scores) >= 1
    }

    return dict(sorted(weights.items(), key=lambda x: x[1], reverse=True))


def _compute_director_affinities(
    movies: list[Movie],
    ratings: list[Rating],
) -> dict[str, float]:

    director_scores: dict[str, list[float]] = defaultdict(list)

    for movie, rating in zip(movies, ratings):
        if movie.director:
            normalised = (rating.score - 0.5) / 4.5
            director_scores[movie.director].append(normalised)

    affinities = {
        director: round(sum(scores) / len(scores), 3)
        for director, scores in director_scores.items()
        if len(scores) >= 2
    }

    return dict(
        sorted(affinities.items(), key=lambda x: x[1], reverse=True)[:20]
    )


def _compute_mood_weights(
    movies: list[Movie],
    ratings: list[Rating],
) -> dict[str, float]:

    mood_scores: dict[str, list[float]] = defaultdict(list)

    for movie, rating in zip(movies, ratings):
        normalised = (rating.score - 0.5) / 4.5
        for tag in (movie.mood_tags or []):
            mood_scores[tag].append(normalised)

    weights = {
        tag: round(sum(scores) / len(scores), 3)
        for tag, scores in mood_scores.items()
    }

    return dict(sorted(weights.items(), key=lambda x: x[1], reverse=True)[:20])