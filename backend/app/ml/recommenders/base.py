"""
app/ml/recommenders/base.py
─────────────────────────────
Abstract interface for all recommenders.
Enforces a consistent return shape so the hybrid ranker
can consume any engine's output without special-casing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class MovieScore:
    """
    Standardised score container.
    Every recommender returns a list of these.
    """
    tmdb_id: int
    score: float                          # 0.0–1.0 normalised
    signal: str                           # "semantic" | "content" | "collaborative"
    metadata: dict = field(default_factory=dict)  # Signal-specific extra data


class BaseRecommender(ABC):
    """
    Every recommender must implement recommend().
    Input is always a user context dict — engines use only the fields they need,
    so they remain independently useful and testable.
    """

    @abstractmethod
    async def recommend(
        self,
        user_context: dict,
        exclude_ids: set[int] | None = None,
        top_k: int = 50,
    ) -> list[MovieScore]:
        """
        Compute recommendations for a user.

        Args:
            user_context: Dict with user data. Engines read from this:
                - user_id (str)
                - embedding_centroid (list[float] | None)
                - genre_weights (dict)
                - rated_movie_ids (list[int])
                - watchlist_movie_ids (list[int])
                - hybrid_weights (dict)

            exclude_ids: Set of tmdb_ids to exclude (already seen, in watchlist, etc.)
            top_k: Number of candidates to return.

        Returns:
            List of MovieScore sorted by score descending.
        """
        ...
