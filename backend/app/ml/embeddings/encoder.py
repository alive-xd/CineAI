"""
app/ml/embeddings/encoder.py
──────────────────────────────
Advanced semantic embedding encoder for CineAI.

Improvements:
- Emotional semantic understanding
- Tone-aware retrieval
- Theme-aware recommendations
- Better pacing similarity
- Reduced title overfitting
- Better psychological matching
- Better cinematic atmosphere retrieval
"""

import logging
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_encoder() -> SentenceTransformer:

    logger.info(
        f"Loading sentence-transformers model: "
        f"{settings.EMBEDDING_MODEL}"
    )

    model = SentenceTransformer(
        settings.EMBEDDING_MODEL
    )

    logger.info(
        "Embedding model loaded"
    )

    return model


def encode_texts(
    texts: list[str],
    batch_size: int = settings.EMBEDDING_BATCH_SIZE,
    normalize: bool = True,
) -> np.ndarray:

    encoder = get_encoder()

    embeddings = encoder.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=len(texts) > 50,
        normalize_embeddings=normalize,
        convert_to_numpy=True,
    )

    return embeddings.astype(np.float32)


def encode_single(text: str) -> list[float]:

    vectors = encode_texts(
        [text],
        batch_size=1,
    )

    return vectors[0].tolist()


def build_movie_text(
    movie_data: dict,
) -> str:
    """
    Advanced semantic movie representation.

    Optimized for:
    - emotional retrieval
    - thematic similarity
    - tone matching
    - pacing awareness
    - psychological recommendation quality
    """

    parts = []

    # ─────────────────────────────────────────────
    # OVERVIEW FIRST (highest semantic value)
    # ─────────────────────────────────────────────

    overview = movie_data.get(
        "overview",
        "",
    )

    if overview:

        parts.append(
            f"Story: {overview}."
        )

    # ─────────────────────────────────────────────
    # GENRES
    # ─────────────────────────────────────────────

    genres = movie_data.get(
        "genres",
        [],
    )

    if genres:

        parts.append(
            "Genres: "
            + ", ".join(genres)
            + "."
        )

    # ─────────────────────────────────────────────
    # THEMES
    # ─────────────────────────────────────────────

    theme_tags = movie_data.get(
        "theme_tags",
        [],
    )

    if theme_tags:

        parts.append(
            "Themes: "
            + ", ".join(theme_tags)
            + "."
        )

    # ─────────────────────────────────────────────
    # MOOD
    # ─────────────────────────────────────────────

    mood_tags = movie_data.get(
        "mood_tags",
        [],
    )

    if mood_tags:

        parts.append(
            "Mood: "
            + ", ".join(mood_tags)
            + "."
        )

    # ─────────────────────────────────────────────
    # TONE
    # ─────────────────────────────────────────────

    tone_tags = movie_data.get(
        "tone_tags",
        [],
    )

    if tone_tags:

        parts.append(
            "Tone: "
            + ", ".join(tone_tags)
            + "."
        )

    # ─────────────────────────────────────────────
    # EMOTIONAL IMPACT
    # ─────────────────────────────────────────────

    emotion_tags = movie_data.get(
        "emotion_tags",
        [],
    )

    if emotion_tags:

        parts.append(
            "Emotion: "
            + ", ".join(emotion_tags)
            + "."
        )

    # ─────────────────────────────────────────────
    # PACING
    # ─────────────────────────────────────────────

    pacing_tags = movie_data.get(
        "pacing_tags",
        [],
    )

    if pacing_tags:

        parts.append(
            "Pacing: "
            + ", ".join(pacing_tags)
            + "."
        )

    # ─────────────────────────────────────────────
    # KEYWORDS
    # ─────────────────────────────────────────────

    keywords = movie_data.get(
        "keywords",
        [],
    )

    if keywords:

        cleaned_keywords = [
            str(k).replace("-", " ")
            for k in keywords[:20]
        ]

        parts.append(
            "Keywords: "
            + ", ".join(cleaned_keywords)
            + "."
        )

    # ─────────────────────────────────────────────
    # DIRECTOR
    # ─────────────────────────────────────────────

    director = movie_data.get(
        "director"
    )

    if not director:

        crew = movie_data.get(
            "crew",
            [],
        )

        for c in crew:

            if c.get("job") == "Director":

                director = c.get(
                    "name"
                )

                break

    if director:

        parts.append(
            f"Director: {director}."
        )

    # ─────────────────────────────────────────────
    # CAST
    # ─────────────────────────────────────────────

    cast = (
        movie_data.get("top_cast")
        or [
            c.get("name")
            for c in movie_data.get(
                "cast",
                [],
            )[:5]
            if c.get("name")
        ]
    )

    if cast:

        parts.append(
            "Cast: "
            + ", ".join(cast)
            + "."
        )

    # ─────────────────────────────────────────────
    # TITLE LAST (low influence)
    # ─────────────────────────────────────────────

    title = movie_data.get(
        "title",
        "",
    )

    if title:

        parts.append(
            f"Movie title: {title}."
        )

    # ─────────────────────────────────────────────
    # YEAR
    # ─────────────────────────────────────────────

    year = movie_data.get(
        "year"
    )

    if (
        not year
        and movie_data.get(
            "release_date"
        )
    ):

        year = str(
            movie_data[
                "release_date"
            ]
        )[:4]

    if year:

        parts.append(
            f"Released: {year}."
        )

    return " ".join(parts)