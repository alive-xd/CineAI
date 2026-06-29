"""
app/ml/recommenders/content_based.py
───────────────────────────────────────
Content-based filtering engine.

Algorithm:
  1. Build a "content soup" string for each movie:
     genres + director + cast + keywords + mood_tags
  2. Fit TF-IDF matrix over the soup strings
  3. For a user, identify their top-rated movies (score ≥ 3.5)
  4. Average their TF-IDF vectors (weighted by rating)
  5. Compute cosine similarity against all movies
  6. Return top_k candidates

Advantages:
  - Zero cold-start for movies (no rating history needed)
  - Transparent: similar movies share genre/director/cast tokens
  - Supports "more like this" (pass a single movie's vector)

Limitation: does not learn cross-user patterns.
  → Solved by the collaborative filter in the hybrid.

Memory: TF-IDF matrix is computed on demand from DB results.
  At 100K movies this is ~300MB — consider chunking or ANN indexing at scale.
  At 10K movies (typical free-tier usage) it's ~30MB, fully acceptable.
"""

import logging

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.ml.recommenders.base import BaseRecommender, MovieScore

logger = logging.getLogger(__name__)


def _build_soup(movie: dict) -> str:
    """
    Build the content fingerprint string for a movie.
    Tokens are space-separated; multi-word names use underscores
    so "Christopher Nolan" becomes "christopher_nolan" (single token).
    """
    parts = []

    # Genres (3× weight by repetition)
    for genre in (movie.get("genres") or []):
        token = genre.lower().replace(" ", "_")
        parts.extend([token] * 3)

    # Director (2× weight)
    director = movie.get("director")
    if not director:
        for c in (movie.get("crew") or []):
            if c.get("job") == "Director":
                director = c.get("name")
                break
    if director:
        d_token = director.lower().replace(" ", "_")
        parts.extend([d_token] * 2)

    # Top 5 cast
    cast = movie.get("top_cast") or [
        c.get("name") for c in (movie.get("cast") or [])[:5] if c.get("name")
    ]
    for actor in cast:
        parts.append(actor.lower().replace(" ", "_"))

    # Keywords and mood tags
    for kw in (movie.get("keywords") or [])[:15]:
        parts.append(kw.lower().replace(" ", "_"))

    for tag in (movie.get("mood_tags") or []):
        parts.append(tag.lower().replace(" ", "_"))

    return " ".join(parts)


class ContentBasedRecommender(BaseRecommender):
    """
    TF-IDF content-based recommender.
    Accepts a pre-built movie corpus (list of movie dicts) at construction time.
    This corpus is refreshed by the recommendation service when stale.
    """

    def __init__(self, movie_corpus: list[dict]) -> None:
        """
        Args:
            movie_corpus: List of movie dicts with keys:
                tmdb_id, genres, crew, cast, keywords, mood_tags, director
        """
        self._corpus = movie_corpus
        self._tmdb_ids = [m["tmdb_id"] for m in movie_corpus]
        self._id_to_idx = {mid: i for i, mid in enumerate(self._tmdb_ids)}
        self._tfidf_matrix = None
        self._vectorizer = None
        self._fit()

    def _fit(self) -> None:
        """Build TF-IDF matrix from the corpus."""
        if not self._corpus:
            return

        soups = [_build_soup(m) for m in self._corpus]

        self._vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),    # Unigrams + bigrams
            min_df=2,              # Ignore tokens appearing in < 2 movies
            max_df=0.95,           # Ignore tokens in > 95% of movies (too common)
            sublinear_tf=True,     # Log normalization of term frequency
        )

        self._tfidf_matrix = self._vectorizer.fit_transform(soups)
        logger.debug(f"TF-IDF matrix shape: {self._tfidf_matrix.shape}")

    async def recommend(
        self,
        user_context: dict,
        exclude_ids: set[int] | None = None,
        top_k: int = 50,
    ) -> list[MovieScore]:
        if self._tfidf_matrix is None:
            return []

        genre_weights = user_context.get("genre_weights", {})
        rated_movies = user_context.get("rated_movies", [])  # list of {movie_id, score}

        # Filter to positively-rated movies (score ≥ 3.5)
        liked_movie_ids = [
            m["movie_id"] for m in rated_movies
            if m["score"] >= 3.5 and m["movie_id"] in self._id_to_idx
        ]

        if not liked_movie_ids:
            # Cold start: fall back to genre-based popularity ranking
            return self._genre_popularity_fallback(genre_weights, exclude_ids, top_k)

        # Build user profile vector: weighted average of liked movie TF-IDF vectors
        liked_indices = [self._id_to_idx[mid] for mid in liked_movie_ids]
        liked_vectors = self._tfidf_matrix[liked_indices]

        # Weight by rating score
        rating_scores = np.array([
            next((m["score"] for m in rated_movies if m["movie_id"] == mid), 3.5)
            for mid in liked_movie_ids
        ])
        weights = (rating_scores - 0.5) / 4.5
        weights = weights / weights.sum()

        # Weighted average
        user_vector = np.asarray(liked_vectors.multiply(weights[:, None]).sum(axis=0))

        # Compute cosine similarity against all movies
        sim_scores = cosine_similarity(user_vector, self._tfidf_matrix).flatten()

        # Build results excluding already-seen movies
        results = []
        for idx, score in enumerate(sim_scores):
            tmdb_id = self._tmdb_ids[idx]
            if exclude_ids and tmdb_id in exclude_ids:
                continue
            results.append(
                MovieScore(
                    tmdb_id=tmdb_id,
                    score=float(score),
                    signal="content",
                    metadata={"genres": self._corpus[idx].get("genres", [])},
                )
            )

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def get_similar_to_movie(
        self,
        movie_id: int,
        top_k: int = 20,
        exclude_ids: set[int] | None = None,
    ) -> list[MovieScore]:
        """
        "More like this" endpoint — find movies similar to a specific movie.
        Used for the similar movies section on the detail page.
        """
        if self._tfidf_matrix is None or movie_id not in self._id_to_idx:
            return []

        idx = self._id_to_idx[movie_id]
        movie_vector = self._tfidf_matrix[idx]
        sim_scores = cosine_similarity(movie_vector, self._tfidf_matrix).flatten()

        results = []
        for i, score in enumerate(sim_scores):
            tmdb_id = self._tmdb_ids[i]
            if tmdb_id == movie_id:
                continue
            if exclude_ids and tmdb_id in exclude_ids:
                continue
            results.append(
                MovieScore(
                    tmdb_id=tmdb_id,
                    score=float(score),
                    signal="content",
                    metadata={
                        "genres": self._corpus[i].get("genres", []),
                        "director": self._corpus[i].get("director"),
                    },
                )
            )

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def _genre_popularity_fallback(
        self,
        genre_weights: dict[str, float],
        exclude_ids: set[int] | None,
        top_k: int,
    ) -> list[MovieScore]:
        """
        Cold start fallback: score movies by genre affinity weights.
        Used when user has no rating history.
        """
        if not genre_weights:
            return []

        results = []
        for movie in self._corpus:
            tmdb_id = movie["tmdb_id"]
            if exclude_ids and tmdb_id in exclude_ids:
                continue

            # Sum affinity weights for this movie's genres
            genre_score = sum(
                genre_weights.get(g, 0.0) for g in (movie.get("genres") or [])
            )
            if genre_score > 0:
                results.append(
                    MovieScore(
                        tmdb_id=tmdb_id,
                        score=min(genre_score / 3.0, 1.0),  # cap at 1.0
                        signal="content",
                        metadata={"genres": movie.get("genres", [])},
                    )
                )

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
