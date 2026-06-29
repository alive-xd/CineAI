"""
app/ml/recommenders/semantic.py
─────────────────────────────────
Improved semantic recommender with
hybrid weighted reranking +
diversity reranking +
metadata-aware search reranking +
query understanding (intent detection,
query expansion, similar-to handling).
"""

import logging
import re
from datetime import datetime

from rapidfuzz import fuzz

from app.integrations.qdrant_client import search_similar_movies
from app.ml.recommenders.base import BaseRecommender, MovieScore

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────
# STOPWORDS
# ─────────────────────────────────────────────────────

_SEARCH_STOPWORDS = {
    "movies", "movie", "film", "films", "about", "with",
    "the", "a", "an", "some", "show", "me", "find", "like",
    "good", "great", "best", "want", "watch", "give", "that",
    "are", "have", "featuring", "something", "looking", "for",
    "something", "ones", "type", "kind", "similar", "more",
}


# ─────────────────────────────────────────────────────
# QUERY EXPANSION MAP
# concept → related tags to also match against
# ─────────────────────────────────────────────────────

_EXPANSION_MAP: dict[str, list[str]] = {
    # Emotions / moods
    "lonely":       ["isolation", "solitude", "alienation", "loneliness"],
    "sad":          ["melancholic", "grief", "sorrow", "emotional", "heartbreak"],
    "scary":        ["horror", "dread", "tension", "fear", "unsettling", "terrifying"],
    "funny":        ["comedy", "humor", "lighthearted", "witty", "hilarious"],
    "dark":         ["gritty", "noir", "bleak", "disturbing", "sinister"],
    "feel":         ["emotional", "heartwarming", "touching", "uplifting"],
    "happy":        ["uplifting", "joyful", "heartwarming", "feel-good"],
    "tense":        ["suspense", "thriller", "anxiety", "edge-of-seat"],
    "romantic":     ["romance", "love", "passion", "relationship"],
    "violent":      ["brutal", "action", "intense", "gritty"],
    "mysterious":   ["mystery", "enigmatic", "suspense", "intrigue"],
    "inspiring":    ["uplifting", "motivational", "triumph", "hope"],

    # Themes
    "identity":     ["self-discovery", "transformation", "purpose", "personal growth"],
    "revenge":      ["vengeance", "justice", "retribution", "payback"],
    "survival":     ["endurance", "struggle", "resilience", "escape"],
    "family":       ["relationships", "parenthood", "bonds", "home"],
    "war":          ["conflict", "battle", "military", "combat"],
    "power":        ["corruption", "ambition", "control", "dominance"],
    "loss":         ["grief", "tragedy", "death", "mourning"],
    "redemption":   ["forgiveness", "second chance", "atonement", "growth"],
    "coming":       ["coming-of-age", "youth", "adolescence", "growth"],

    # Style / tone
    "mindbending":  ["psychological", "twist", "surreal", "nonlinear", "complex"],
    "psychological": ["mind-bending", "surreal", "disturbing", "complex", "twist"],
    "slow":         ["slow-burn", "atmospheric", "contemplative", "meditative"],
    "fast":         ["fast-paced", "action", "thrilling", "adrenaline"],
    "realistic":    ["gritty", "raw", "authentic", "naturalistic"],
    "epic":         ["grand", "sweeping", "large-scale", "ambitious"],

    # Genres (common misspellings / casual terms)
    "scifi":        ["science fiction", "sci-fi", "futuristic", "space"],
    "horror":       ["scary", "terror", "supernatural", "slasher"],
    "thriller":     ["suspense", "tension", "mystery", "crime"],
    "drama":        ["emotional", "character-driven", "realistic"],
    "action":       ["adventure", "fast-paced", "intense", "explosive"],
    "animation":    ["animated", "cartoon", "family"],
}


# ─────────────────────────────────────────────────────
# SIMILAR-TO PATTERNS
# detect "like X", "similar to X", "reminds me of X"
# ─────────────────────────────────────────────────────

_SIMILAR_TO_PATTERNS = [
    r"(?:like|similar to|reminds? me of|in the style of|along the lines of)\s+(.+?)(?:\s+but|\s+except|\s+only|$)",
    r"(?:another|more)\s+(.+?)(?:\s+type|\s+style|\s+kind|$)",
]


# ─────────────────────────────────────────────────────
# INTENT DETECTION
# ─────────────────────────────────────────────────────

_MOOD_KEYWORDS = {
    "sad", "happy", "funny", "scary", "dark", "romantic",
    "tense", "relaxing", "feel", "mood", "emotional", "uplifting",
    "depressing", "hopeful", "lonely", "inspiring",
}

_THEME_KEYWORDS = {
    "identity", "revenge", "survival", "family", "war", "power",
    "loss", "redemption", "coming", "meaning", "purpose", "corruption",
    "justice", "freedom", "love", "death", "grief",
}

_GENRE_KEYWORDS = {
    "action", "comedy", "drama", "horror", "thriller", "romance",
    "scifi", "sci-fi", "animation", "documentary", "fantasy",
    "mystery", "western", "musical",
}


def detect_intent(query: str) -> str:
    """
    Classify the search intent into one of:
    - similar_to : user wants movies like a specific title
    - mood       : user describes an emotional experience
    - theme      : user describes a topic or subject
    - genre      : user names a genre
    - general    : catch-all
    """
    q = query.lower()

    # Check similar-to first (most specific)
    for pattern in _SIMILAR_TO_PATTERNS:
        if re.search(pattern, q):
            return "similar_to"

    tokens = set(re.findall(r"\b[a-z]+\b", q))

    if tokens & _MOOD_KEYWORDS:
        return "mood"

    if tokens & _THEME_KEYWORDS:
        return "theme"

    if tokens & _GENRE_KEYWORDS:
        return "genre"

    return "general"


def extract_similar_to_title(query: str) -> str | None:
    """
    Extract the movie title from a 'similar to X' query.
    e.g. "something like Inception" → "Inception"
    """
    for pattern in _SIMILAR_TO_PATTERNS:
        match = re.search(pattern, query.lower())
        if match:
            title = match.group(1).strip()
            # Clean trailing noise words
            title = re.sub(
                r"\s+(but|except|only|more|another|type|style|kind).*$",
                "",
                title,
            ).strip()
            return title.title() if title else None
    return None


def expand_concepts(concepts: list[str]) -> list[str]:
    """
    Expand concept tokens using the expansion map.
    Returns original concepts + expanded terms, deduplicated.
    """
    expanded = list(concepts)
    for concept in concepts:
        expansions = _EXPANSION_MAP.get(concept, [])
        for term in expansions:
            if term not in expanded:
                expanded.append(term)
    return expanded


# ─────────────────────────────────────────────────────
# RECOMMENDER
# ─────────────────────────────────────────────────────

class SemanticRecommender(BaseRecommender):

    def _normalize_vote_score(self, vote_average: float) -> float:
        return min(max(vote_average / 10.0, 0), 1)

    def _normalize_popularity(self, popularity: float) -> float:
        return min(popularity / 100.0, 1)

    def _normalize_recency(self, year: int | None) -> float:
        if not year:
            return 0.3
        age = datetime.now().year - year
        if age <= 3:
            return 1.0
        if age <= 10:
            return 0.8
        if age <= 20:
            return 0.6
        return 0.4

    def _hybrid_score(
        self,
        semantic_score: float,
        vote_average: float,
        popularity: float,
        year: int | None,
    ) -> float:
        vote_score = self._normalize_vote_score(vote_average)
        popularity_score = self._normalize_popularity(popularity)
        recency_score = self._normalize_recency(year)

        return round(
            semantic_score * 0.65
            + vote_score * 0.15
            + popularity_score * 0.10
            + recency_score * 0.10,
            4,
        )

    def _search_hybrid_score(
        self,
        semantic_score: float,
        vote_average: float,
        popularity: float,
        year: int | None,
        metadata_boost: float,
    ) -> float:
        vote_score = self._normalize_vote_score(vote_average)
        popularity_score = self._normalize_popularity(popularity)
        recency_score = self._normalize_recency(year)

        base_score = (
            semantic_score * 0.55
            + vote_score * 0.12
            + popularity_score * 0.08
            + recency_score * 0.05
        )

        return round(min(base_score + metadata_boost, 1.0), 4)

    def _extract_concepts(self, query: str) -> list[str]:
        tokens = re.findall(r"\b[a-z]+\b", query.lower())
        return [
            t for t in tokens
            if t not in _SEARCH_STOPWORDS and len(t) > 3
        ]

    def _compute_metadata_boost(
        self,
        hit: dict,
        concepts: list[str],
    ) -> float:
        if not concepts:
            return 0.0

        all_tags: list[str] = []
        for field in ("theme_tags", "mood_tags", "tone_tags", "emotion_tags"):
            all_tags.extend(hit.get(field, []))

        if not all_tags:
            return 0.0

        tags_lower = [t.lower() for t in all_tags]
        boost = 0.0

        for concept in concepts:
            for tag in tags_lower:
                if concept in tag or tag in concept:
                    boost += 0.15
                elif fuzz.ratio(concept, tag) > 75:
                    boost += 0.08

        return min(boost, 0.40)

    def _apply_diversity_reranking(
        self,
        scores: list[MovieScore],
        top_k: int,
    ) -> list[MovieScore]:
        scores.sort(key=lambda x: x.score, reverse=True)

        genre_counts: dict[str, int] = {}
        diversified_scores = []

        for item in scores:
            genres = item.metadata.get("genres", [])
            diversity_penalty = sum(
                genre_counts.get(g, 0) * 0.03 for g in genres
            )
            item.score = max(item.score - diversity_penalty, 0)
            diversified_scores.append(item)
            for g in genres:
                genre_counts[g] = genre_counts.get(g, 0) + 1

        diversified_scores.sort(key=lambda x: x.score, reverse=True)
        return diversified_scores[:top_k]

    async def recommend(
        self,
        user_context: dict,
        exclude_ids: set[int] | None = None,
        top_k: int = 50,
    ) -> list[MovieScore]:

        centroid = user_context.get("embedding_centroid")

        if centroid is None:
            logger.debug("No user centroid — semantic recommender returning empty")
            return []

        results = await search_similar_movies(
            query_vector=centroid,
            top_k=max(top_k * 3, 100),
            score_threshold=0.08,
        )

        logger.info(f"Raw semantic results: {len(results)}")

        scores = []

        for hit in results:
            tmdb_id = hit.get("tmdb_id")
            if not tmdb_id:
                continue
            if exclude_ids and tmdb_id in exclude_ids:
                continue

            semantic_score = float(hit.get("score", 0))
            vote_average = float(hit.get("vote_average", 0))
            popularity = float(hit.get("popularity", 0))
            year = hit.get("year")

            hybrid_score = self._hybrid_score(
                semantic_score=semantic_score,
                vote_average=vote_average,
                popularity=popularity,
                year=year,
            )

            scores.append(MovieScore(
                tmdb_id=tmdb_id,
                score=hybrid_score,
                signal="semantic_hybrid",
                metadata={
                    "title": hit.get("title"),
                    "genres": hit.get("genres", []),
                    "year": year,
                    "vote_average": vote_average,
                    "popularity": popularity,
                    "semantic_score": semantic_score,
                    "hybrid_score": hybrid_score,
                },
            ))

        final_scores = self._apply_diversity_reranking(scores=scores, top_k=top_k)
        logger.info(f"Hybrid reranked {len(final_scores)} results")
        return final_scores

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 20,
        filters: dict | None = None,
        exclude_ids: set[int] | None = None,
        query: str | None = None,
    ) -> list[MovieScore]:
        """
        Query-based semantic search with
        metadata-aware reranking + query understanding.
        """

        results = await search_similar_movies(
            query_vector=query_vector,
            top_k=max(top_k * 3, 50),
            score_threshold=0.08,
            filters=filters,
        )

        logger.info(f"Raw semantic hits: {len(results)}")

        # ── Query understanding ────────────────────────────
        concepts: list[str] = []
        intent = "general"
        similar_to_title: str | None = None

        if query:
            intent = detect_intent(query)
            raw_concepts = self._extract_concepts(query)
            concepts = expand_concepts(raw_concepts)

            if intent == "similar_to":
                similar_to_title = extract_similar_to_title(query)

            logger.info(
                f"Query intent={intent} "
                f"concepts={raw_concepts} "
                f"expanded={concepts} "
                f"similar_to={similar_to_title}"
            )

        scores = []

        for hit in results:
            tmdb_id = hit.get("tmdb_id")
            if not tmdb_id:
                continue
            if exclude_ids and tmdb_id in exclude_ids:
                continue

            semantic_score = float(hit.get("score", 0))
            vote_average = float(hit.get("vote_average", 0))
            popularity = float(hit.get("popularity", 0))
            year = hit.get("year")

            metadata_boost = self._compute_metadata_boost(
                hit=hit,
                concepts=concepts,
            )

            # For similar_to intent: boost exact title matches
            if similar_to_title:
                title = (hit.get("title") or "").lower()
                if similar_to_title.lower() in title:
                    metadata_boost = min(metadata_boost + 0.30, 0.40)

            hybrid_score = self._search_hybrid_score(
                semantic_score=semantic_score,
                vote_average=vote_average,
                popularity=popularity,
                year=year,
                metadata_boost=metadata_boost,
            )

            scores.append(MovieScore(
                tmdb_id=tmdb_id,
                score=hybrid_score,
                signal="semantic_hybrid",
                metadata={
                    "title": hit.get("title"),
                    "genres": hit.get("genres", []),
                    "year": year,
                    "vote_average": vote_average,
                    "popularity": popularity,
                    "semantic_score": semantic_score,
                    "metadata_boost": metadata_boost,
                    "intent": intent,
                    "hybrid_score": hybrid_score,
                },
            ))

        final_scores = self._apply_diversity_reranking(scores=scores, top_k=top_k)
        logger.info(f"Final reranked results: {len(final_scores)}")
        return final_scores