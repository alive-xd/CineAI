"""
app/ml/explainability/explainer.py
────────────────────────────────────
Advanced recommendation explainability engine.

Features:
- semantic explanations
- emotional explanations
- collaborative explanations
- preference-aware reasoning
- mood-aware reasoning
- pacing-aware reasoning
- tone/theme-aware reasoning
- cinematic atmosphere explanations
- confidence scoring
"""

import logging
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.movie import Movie

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────
# MATCH LABELS
# ─────────────────────────────────────────────────────

LABEL_THRESHOLDS = [
    (0.85, "Exceptional match"),
    (0.75, "Perfect match"),
    (0.60, "Great pick"),
    (0.45, "You might love this"),
    (0.30, "Worth exploring"),
    (0.00, "Discovering something new"),
]


def get_match_label(composite_score: float) -> str:
    for threshold, label in LABEL_THRESHOLDS:
        if composite_score >= threshold:
            return label
    return "Discovering something new"


# ─────────────────────────────────────────────────────
# CONFIDENCE
# ─────────────────────────────────────────────────────

def compute_confidence(composite_score: float) -> float:
    x = (composite_score - 0.5) * 8
    sigmoid = 1 / (1 + math.exp(-x))
    return round(0.3 + sigmoid * 0.65, 2)


def dominant_signal(scores: dict[str, float]) -> str:
    return max(scores, key=lambda k: scores[k])


# ─────────────────────────────────────────────────────
# SEMANTIC REASONS
# ─────────────────────────────────────────────────────

def _semantic_reasons(
    semantic_score: float,
    user_context: dict,
    movie: "Movie",
) -> list[str]:

    # FIX 1: lowered threshold 0.35 → 0.15
    # so more recommendations get personal reasons
    # instead of falling back to generic copy
    if semantic_score < 0.15:
        return []

    reasons = []

    genre_weights = user_context.get("genre_weights", {})
    mood_weights = user_context.get("mood_tag_weights", {})

    # Genre affinity
    matched_genres = [
        g for g in (movie.genres or [])
        if genre_weights.get(g, 0) >= 0.6
    ]
    if matched_genres:
        reasons.append(
            f"Matches your love of "
            f"{' · '.join(matched_genres[:2])}"
        )

    # Mood affinity
    matched_moods = [
        t for t in (movie.mood_tags or [])
        if mood_weights.get(t, 0) >= 0.6
    ]
    if matched_moods:
        reasons.append(
            f"{' · '.join(matched_moods[:2]).capitalize()} "
            f"themes you consistently enjoy"
        )

    # FIX 3a: tone tags (were ignored before)
    tone_tags = movie.tone_tags or []
    if tone_tags:
        reasons.append(
            f"{tone_tags[0].capitalize()} tone "
            f"that matches your taste"
        )

    # FIX 3b: theme tags (were ignored before)
    theme_tags = movie.theme_tags or []
    if theme_tags:
        reasons.append(
            f"Explores "
            f"{' · '.join(theme_tags[:2])} "
            f"themes"
        )

    # Emotional atmosphere
    emotion_tags = movie.emotion_tags or []
    if emotion_tags:
        reasons.append(
            f"Strong "
            f"{' · '.join(emotion_tags[:2])} "
            f"emotional atmosphere"
        )

    # Pacing
    pacing_tags = movie.pacing_tags or []
    if pacing_tags:
        reasons.append(
            f"{pacing_tags[0].capitalize()} pacing "
            f"that fits your viewing style"
        )

    # Strong semantic fallback
    if semantic_score >= 0.80 and not reasons:
        reasons.append(
            "Extremely close to your overall cinematic taste"
        )

    return reasons[:3]


# ─────────────────────────────────────────────────────
# CONTENT REASONS
# ─────────────────────────────────────────────────────

def _content_reasons(
    content_score: float,
    user_context: dict,
    movie: "Movie",
) -> list[str]:

    if content_score < 0.35:
        return []

    reasons = []

    director_affinities = user_context.get("director_affinities", {})
    liked_movie_titles = user_context.get("liked_movie_titles", [])

    # Director affinity
    director = movie.director
    if director and director_affinities.get(director, 0) >= 0.65:
        reasons.append(f"You strongly enjoy films by {director}")

    # Genre overlap
    genre_weights = user_context.get("genre_weights", {})
    top_genres = [
        g for g in (movie.genres or [])
        if genre_weights.get(g, 0) >= 0.55
    ]
    if top_genres:
        reasons.append(
            f"{' & '.join(top_genres[:2])} "
            f"are among your highest-rated genres"
        )

    # FIX 2: match liked title to the movie's genres/mood
    # instead of always using liked_movie_titles[0]
    if liked_movie_titles and content_score >= 0.60:
        best_title = _match_liked_title(
            movie,
            liked_movie_titles,
            user_context.get("liked_movie_genres", {}),
        )
        if best_title:
            reasons.append(
                f"Similar cinematic feel to {best_title}"
            )

    # Theme tags
    if movie.theme_tags:
        reasons.append(
            f"Explores "
            f"{' · '.join(movie.theme_tags[:2])} "
            f"themes"
        )

    return reasons[:3]


def _match_liked_title(
    movie: "Movie",
    liked_titles: list[str],
    liked_movie_genres: dict[str, list[str]],
) -> str | None:
    """
    Pick the most relevant liked title for this movie
    based on genre overlap, instead of always picking index 0.
    Falls back to index 0 if no genre data available.
    """
    if not liked_movie_genres:
        return liked_titles[0] if liked_titles else None

    movie_genres = set(movie.genres or [])
    best_title = None
    best_overlap = -1

    for title in liked_titles:
        title_genres = set(liked_movie_genres.get(title, []))
        overlap = len(movie_genres & title_genres)
        if overlap > best_overlap:
            best_overlap = overlap
            best_title = title

    return best_title or liked_titles[0]


# ─────────────────────────────────────────────────────
# COLLABORATIVE REASONS
# ─────────────────────────────────────────────────────

def _collab_reasons(
    collab_score: float,
    user_context: dict,
) -> list[str]:

    if collab_score < 0.45:
        return []

    # FIX 4: removed misleading {total_ratings} reference
    # (was showing current user's rating count, not similar users')
    if collab_score >= 0.80:
        return ["Exceptionally strong match with viewers like you"]

    if collab_score >= 0.65:
        return ["Highly rated by viewers with very similar taste"]

    if collab_score >= 0.50:
        return ["Frequently loved by viewers with similar preferences"]

    return ["Recommended based on similar viewing patterns"]


# ─────────────────────────────────────────────────────
# POPULARITY REASONS
# ─────────────────────────────────────────────────────

def _popularity_reasons(
    popularity_score: float,
    movie: "Movie",
) -> list[str]:

    if popularity_score < 0.70:
        return []

    if movie.vote_average >= 8.5:
        return [f"Universally acclaimed ({movie.vote_average:.1f}/10)"]

    if movie.vote_average >= 8.0:
        return [
            f"Critically praised "
            f"({movie.vote_average:.1f}/10 "
            f"from {movie.vote_count:,} votes)"
        ]

    if movie.popularity > 500:
        return ["Trending strongly among audiences"]

    return ["Widely praised by movie fans"]


# ─────────────────────────────────────────────────────
# FALLBACK
# ─────────────────────────────────────────────────────

def _fallback_reason(movie: "Movie") -> str:
    if movie.vote_average >= 7.5:
        return (
            f"Highly rated "
            f"{(movie.genres or ['film'])[0].lower()}"
        )
    if movie.genres:
        return f"A compelling {movie.genres[0].lower()} experience"
    return "Expanding your cinematic taste"


# ─────────────────────────────────────────────────────
# MAIN EXPLAINER
# ─────────────────────────────────────────────────────

def explain_recommendation(
    movie: "Movie",
    scores: dict[str, float],
    user_context: dict,
) -> dict:

    all_reasons: list[str] = []

    dom = dominant_signal({
        "semantic": scores.get("semantic", 0),
        "content": scores.get("content", 0),
        "collaborative": scores.get("collaborative", 0),
        "popularity": scores.get("popularity", 0),
    })

    all_reasons.extend(
        _semantic_reasons(scores.get("semantic", 0), user_context, movie)
    )
    all_reasons.extend(
        _content_reasons(scores.get("content", 0), user_context, movie)
    )
    all_reasons.extend(
        _collab_reasons(scores.get("collaborative", 0), user_context)
    )
    all_reasons.extend(
        _popularity_reasons(scores.get("popularity", 0), movie)
    )

    # Deduplicate
    seen: set[str] = set()
    unique_reasons: list[str] = []
    for reason in all_reasons:
        if reason not in seen:
            seen.add(reason)
            unique_reasons.append(reason)

    if not unique_reasons:
        unique_reasons = [_fallback_reason(movie)]

    composite = scores.get("composite", 0.0)

    return {
        "reasons": unique_reasons[:4],
        "confidence": compute_confidence(composite),
        "match_label": get_match_label(composite),
        "dominant_signal": dom,
        "score_breakdown": {
            "semantic": round(scores.get("semantic", 0), 3),
            "content": round(scores.get("content", 0), 3),
            "collaborative": round(scores.get("collaborative", 0), 3),
            "popularity": round(scores.get("popularity", 0), 3),
            "composite": round(composite, 3),
        },
    }


# ─────────────────────────────────────────────────────
# SIMILAR MOVIE EXPLAINER
# ─────────────────────────────────────────────────────

def explain_similar_movie(
    source_movie: "Movie",
    target_movie: "Movie",
    similarity_score: float,
    shared_attributes: list[str],
) -> dict:

    reasons = []

    if (
        source_movie.director
        and source_movie.director == target_movie.director
    ):
        reasons.append(f"Also directed by {source_movie.director}")

    shared_genres = (
        set(source_movie.genres or [])
        & set(target_movie.genres or [])
    )
    if shared_genres:
        reasons.append(
            f"Shared {' & '.join(list(shared_genres)[:2])} genre DNA"
        )

    if shared_attributes:
        for attr in shared_attributes:
            if attr not in reasons:
                reasons.append(attr)

    if not reasons:
        reasons = [f"Similar cinematic experience to {source_movie.title}"]

    return {
        "reasons": reasons[:4],
        "confidence": round(similarity_score, 2),
        "match_label": get_match_label(similarity_score),
        "dominant_signal": "content",
        "score_breakdown": {
            "content": round(similarity_score, 3),
            "semantic": 0.0,
            "collaborative": 0.0,
            "popularity": 0.0,
            "composite": round(similarity_score, 3),
        },
    }