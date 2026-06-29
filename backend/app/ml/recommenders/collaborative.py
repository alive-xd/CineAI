"""
app/ml/recommenders/collaborative.py
──────────────────────────────────────
Collaborative filtering via user-based cosine similarity.

No scikit-surprise required — uses numpy + scikit-learn (already installed).

Pipeline:
  1. Build user-movie ratings matrix from DB
  2. Compute cosine similarity between users
  3. For target user, find top-N similar users
  4. Predict scores for unrated movies via weighted average
  5. Return top-k MovieScore results

Model is cached in memory as a singleton and rebuilt
every 24 hours by the scheduler.
"""

import logging
from datetime import datetime

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.recommenders.base import BaseRecommender, MovieScore

logger = logging.getLogger(__name__)

MIN_RATINGS_FOR_CF = 5
TOP_SIMILAR_USERS = 20


class CollaborativeRecommender(BaseRecommender):

    def __init__(self) -> None:
        self._is_trained = False
        self._user_ids: list[str] = []
        self._movie_ids: list[int] = []
        self._ratings_matrix: np.ndarray | None = None  # shape: (users, movies)
        self._user_index: dict[str, int] = {}
        self._movie_index: dict[int, int] = {}
        self._trained_at: datetime | None = None

    async def train(self, db: AsyncSession) -> dict:
        """
        Build ratings matrix from DB and compute model state.
        Called once at startup and nightly by scheduler.
        """
        result = await db.execute(
            text("SELECT user_id::text, movie_id, score FROM ratings")
        )
        rows = result.fetchall()

        if len(rows) < 10:
            logger.warning("Not enough ratings to train CF model (<10 total)")
            return {"status": "skipped", "reason": "insufficient_data"}

        logger.info(f"Training CF model on {len(rows)} ratings")

        # Build index maps
        user_ids = list({row[0] for row in rows})
        movie_ids = list({row[1] for row in rows})

        self._user_ids = user_ids
        self._movie_ids = movie_ids
        self._user_index = {uid: i for i, uid in enumerate(user_ids)}
        self._movie_index = {mid: i for i, mid in enumerate(movie_ids)}

        # Build ratings matrix (users x movies), 0 = not rated
        matrix = np.zeros(
            (len(user_ids), len(movie_ids)),
            dtype=np.float32,
        )

        for user_id, movie_id, score in rows:
            u = self._user_index.get(user_id)
            m = self._movie_index.get(movie_id)
            if u is not None and m is not None:
                # Normalize score to 0-1
                matrix[u, m] = (score - 0.5) / 4.5

        self._ratings_matrix = matrix
        self._is_trained = True
        self._trained_at = datetime.utcnow()

        logger.info(
            f"CF model trained: {len(user_ids)} users, "
            f"{len(movie_ids)} movies"
        )

        return {
            "status": "trained",
            "n_ratings": len(rows),
            "n_users": len(user_ids),
            "n_items": len(movie_ids),
        }

    async def recommend(
        self,
        user_context: dict,
        exclude_ids: set[int] | None = None,
        top_k: int = 50,
    ) -> list[MovieScore]:

        if not self._is_trained or self._ratings_matrix is None:
            return []

        user_id = str(user_context.get("user_id", ""))
        total_ratings = user_context.get("total_ratings", 0)

        if total_ratings < MIN_RATINGS_FOR_CF:
            return []

        if user_id not in self._user_index:
            return []

        u_idx = self._user_index[user_id]
        user_vector = self._ratings_matrix[u_idx].reshape(1, -1)

        # ── Find similar users ────────────────────────────────────────────
        # Only compare against users who have rated at least one movie
        # in common with the target user
        rated_mask = user_vector[0] > 0
        if not rated_mask.any():
            return []

        # Cosine similarity between target user and all others
        similarities = cosine_similarity(
            user_vector,
            self._ratings_matrix,
        )[0]

        # Exclude self
        similarities[u_idx] = 0.0

        # Top similar users
        similar_user_indices = np.argsort(similarities)[::-1][:TOP_SIMILAR_USERS]
        similar_users = [
            (idx, similarities[idx])
            for idx in similar_user_indices
            if similarities[idx] > 0.1  # minimum similarity threshold
        ]

        if not similar_users:
            return []

        # ── Predict scores for unrated movies ────────────────────────────
        rated_ids = set(user_context.get("rated_movie_ids", []))
        exclude_ids = exclude_ids or set()

        predictions: list[tuple[int, float]] = []

        for m_idx, movie_id in enumerate(self._movie_ids):
            if movie_id in rated_ids or movie_id in exclude_ids:
                continue

            # Weighted average of similar users' ratings
            weighted_sum = 0.0
            weight_total = 0.0

            for u_similar, similarity in similar_users:
                rating = self._ratings_matrix[u_similar, m_idx]
                if rating > 0:
                    weighted_sum += similarity * rating
                    weight_total += similarity

            if weight_total > 0:
                predicted = weighted_sum / weight_total
                predictions.append((movie_id, predicted))

        if not predictions:
            return []

        predictions.sort(key=lambda x: x[1], reverse=True)

        results = []
        for movie_id, score in predictions[:top_k]:
            results.append(MovieScore(
                tmdb_id=movie_id,
                score=round(max(0.0, min(1.0, score)), 4),
                signal="collaborative",
                metadata={"predicted_score": round(score, 3)},
            ))

        logger.debug(f"CF produced {len(results)} recommendations for {user_id}")
        return results

    def predict_single(self, user_id: str, movie_id: int) -> float:
        if not self._is_trained or user_id not in self._user_index:
            return 0.0

        u_idx = self._user_index[user_id]
        m_idx = self._movie_index.get(movie_id)
        if m_idx is None:
            return 0.0

        user_vector = self._ratings_matrix[u_idx].reshape(1, -1)
        similarities = cosine_similarity(user_vector, self._ratings_matrix)[0]
        similarities[u_idx] = 0.0

        similar_indices = np.argsort(similarities)[::-1][:TOP_SIMILAR_USERS]

        weighted_sum = 0.0
        weight_total = 0.0

        for u_similar in similar_indices:
            sim = similarities[u_similar]
            if sim <= 0.1:
                continue
            rating = self._ratings_matrix[u_similar, m_idx]
            if rating > 0:
                weighted_sum += sim * rating
                weight_total += sim

        if weight_total == 0:
            return 0.0

        return round(max(0.0, min(1.0, weighted_sum / weight_total)), 4)


# ── Singleton ─────────────────────────────────────────────────────────────────

_cf_instance: CollaborativeRecommender | None = None


def get_collaborative_recommender() -> CollaborativeRecommender:
    global _cf_instance
    if _cf_instance is None:
        _cf_instance = CollaborativeRecommender()
    return _cf_instance