"""
app/services/movie_service.py
───────────────────────────────
Business logic for movie operations.

Responsibilities:
  - Fetch movies from TMDb and upsert to local DB (cache layer)
  - Derive semantic metadata tags
  - Compute popularity_score
  - Build MovieCardResponse / MovieDetailResponse from ORM objects
"""

import logging
import math
from datetime import date

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.tmdb_client import TMDbClient
from app.models.movie import Movie
from app.schemas import (
    MovieCardResponse,
    MovieDetailResponse,
    MovieSearchFilters,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Genre → mood mapping
# ──────────────────────────────────────────────────────────────────────────────

GENRE_MOOD_MAP: dict[str, list[str]] = {
    "Action": ["high-energy", "intense", "thrilling"],
    "Adventure": ["epic", "exciting", "journey"],
    "Animation": ["fun", "family-friendly", "imaginative"],
    "Comedy": ["light-hearted", "funny", "feel-good"],
    "Crime": ["dark", "suspenseful", "gritty"],
    "Documentary": ["informative", "real", "thought-provoking"],
    "Drama": ["emotional", "character-driven", "deep"],
    "Fantasy": ["imaginative", "magical", "epic"],
    "Horror": ["scary", "dark", "suspenseful"],
    "Mystery": ["suspenseful", "intriguing", "cerebral"],
    "Romance": ["emotional", "feel-good", "heartwarming"],
    "Science Fiction": ["thought-provoking", "mindbending", "futuristic"],
    "Thriller": ["tense", "dark", "suspenseful"],
    "War": ["intense", "emotional", "gritty"],
    "Western": ["classic", "epic", "adventurous"],
}

KEYWORD_MOOD_MAP: dict[str, str] = {
    "time travel": "mindbending",
    "dystopia": "dark",
    "artificial intelligence": "futuristic",
    "heist": "clever",
    "redemption": "emotional",
    "coming of age": "heartwarming",
    "philosophical": "thought-provoking",
    "supernatural": "mysterious",
    "psychological": "cerebral",
    "space": "epic",
}

# ──────────────────────────────────────────────────────────────────────────────
# Advanced semantic tagging
# ──────────────────────────────────────────────────────────────────────────────

THEME_TAG_MAP: dict[str, str] = {
    "time travel": "time travel",
    "space": "space exploration",
    "survival": "survival",
    "revenge": "revenge",
    "grief": "grief",
    "loss": "loss",
    "identity": "identity",
    "war": "war",
    "future": "futurism",
    "artificial intelligence": "ai",
    "robot": "ai",
    "alien": "alien contact",
    "love": "love",
    "friendship": "friendship",
    "murder": "crime",
    "serial killer": "crime",
    "dream": "dreams",
    "memory": "memory",
    "death": "mortality",
}

TONE_TAG_MAP: dict[str, str] = {
    "dark": "dark",
    "gritty": "gritty",
    "hope": "hopeful",
    "hopeful": "hopeful",
    "sad": "melancholic",
    "depressing": "melancholic",
    "emotional": "emotional",
    "tense": "tense",
    "funny": "light-hearted",
    "uplifting": "uplifting",
    "mysterious": "mysterious",
    "philosophical": "philosophical",
}

PACING_TAG_MAP: dict[str, str] = {
    "action": "fast-paced",
    "battle": "fast-paced",
    "war": "intense",
    "thriller": "intense",
    "dialogue": "dialogue-heavy",
    "slow": "slow-burn",
    "mystery": "slow-burn",
    "crime": "methodical",
}

EMOTION_TAG_MAP: dict[str, str] = {
    "sad": "heartbreaking",
    "loss": "emotional",
    "death": "tragic",
    "love": "romantic",
    "fear": "disturbing",
    "terror": "disturbing",
    "hope": "inspirational",
    "survival": "tense",
    "lonely": "lonely",
}


# ──────────────────────────────────────────────────────────────────────────────
# Semantic derivation helpers
# ──────────────────────────────────────────────────────────────────────────────

def derive_mood_tags(
    genres: list[str],
    keywords: list[str],
) -> list[str]:

    moods: set[str] = set()

    for genre in genres:

        for mood in (
            GENRE_MOOD_MAP.get(
                genre,
                [],
            )[:2]
        ):
            moods.add(mood)

    keywords_lower = {
        k.lower()
        for k in keywords
    }

    for kw, mood in (
        KEYWORD_MOOD_MAP.items()
    ):

        if kw in keywords_lower:
            moods.add(mood)

    return list(moods)[:8]


def derive_theme_tags(
    overview: str,
    keywords: list[str],
) -> list[str]:

    themes: set[str] = set()

    text = (
        (
            overview or ""
        ).lower()
        + " "
        + " ".join(keywords).lower()
    )

    for trigger, tag in (
        THEME_TAG_MAP.items()
    ):

        if trigger in text:
            themes.add(tag)

    return list(themes)[:10]


def derive_tone_tags(
    overview: str,
    keywords: list[str],
) -> list[str]:

    tones: set[str] = set()

    text = (
        (
            overview or ""
        ).lower()
        + " "
        + " ".join(keywords).lower()
    )

    for trigger, tag in (
        TONE_TAG_MAP.items()
    ):

        if trigger in text:
            tones.add(tag)

    return list(tones)[:8]


def derive_pacing_tags(
    overview: str,
    genres: list[str],
) -> list[str]:

    pacing: set[str] = set()

    text = (
        (overview or "").lower()
        + " "
        + " ".join(genres).lower()
    )

    for trigger, tag in (
        PACING_TAG_MAP.items()
    ):

        if trigger in text:
            pacing.add(tag)

    return list(pacing)[:6]


def derive_emotion_tags(
    overview: str,
    keywords: list[str],
) -> list[str]:

    emotions: set[str] = set()

    text = (
        (
            overview or ""
        ).lower()
        + " "
        + " ".join(keywords).lower()
    )

    for trigger, tag in (
        EMOTION_TAG_MAP.items()
    ):

        if trigger in text:
            emotions.add(tag)

    return list(emotions)[:8]


# ──────────────────────────────────────────────────────────────────────────────
# Popularity scoring
# ──────────────────────────────────────────────────────────────────────────────

def compute_popularity_score(
    vote_average: float,
    vote_count: int,
    release_date: date | None,
) -> float:

    if vote_count < 10:
        return 0.0

    base = vote_average * math.log(vote_count + 1)

    recency = 1.0

    if release_date:

        age_years = (
            date.today() - release_date
        ).days / 365.25

        if age_years > 10:

            recency = max(
                0.7,
                1.0 - (
                    age_years - 10
                ) * 0.01,
            )

    return round(base * recency, 4)


# ──────────────────────────────────────────────────────────────────────────────
# Movie service
# ──────────────────────────────────────────────────────────────────────────────

class MovieService:

    def __init__(
        self,
        db: AsyncSession,
        tmdb: TMDbClient,
    ) -> None:

        self.db = db
        self.tmdb = tmdb

    async def get_or_fetch_movie(
        self,
        tmdb_id: int,
    ) -> Movie:

        result = await self.db.execute(
            select(Movie).where(
                Movie.tmdb_id == tmdb_id
            )
        )

        movie = result.scalar_one_or_none()

        if movie is None:

            async with self.tmdb as client:

                data = await client.get_movie(
                    tmdb_id
                )

            movie = await self._upsert_movie(
                data
            )

        return movie

    async def get_trending(
        self,
        page: int = 1,
    ) -> list[Movie]:

        async with self.tmdb as client:

            data = await client.get_trending(
                page=page
            )

        movies = []

        for item in data["results"]:

            try:

                full = await self.get_or_fetch_movie(
                    item["tmdb_id"]
                )

                movies.append(full)

            except Exception as exc:

                logger.warning(
                    f"Skipping movie "
                    f"{item.get('tmdb_id')}: "
                    f"{exc}"
                )

        return movies

    async def search_keyword(
        self,
        query: str,
        filters: MovieSearchFilters,
    ) -> list[Movie]:

        async with self.tmdb as client:

            data = await client.search_movies(
                query,
                page=filters.page,
            )

        movies = []

        for item in data["results"]:

            try:

                movie = await self.get_or_fetch_movie(
                    item["tmdb_id"]
                )

                if self._passes_filters(
                    movie,
                    filters,
                ):
                    movies.append(movie)

            except Exception:
                continue

        return movies

    async def get_movies_for_corpus(
        self,
        limit: int = 5000,
    ) -> list[dict]:

        result = await self.db.execute(
            select(Movie)
            .where(Movie.vote_count >= 50)
            .order_by(
                desc(Movie.popularity_score)
            )
            .limit(limit)
        )

        movies = result.scalars().all()

        return [
            {
                "tmdb_id": m.tmdb_id,
                "title": m.title,
                "genres": m.genres,
                "crew": m.crew,
                "cast": m.cast,
                "keywords": m.keywords,
                "mood_tags": m.mood_tags,
                "tone_tags": m.tone_tags,
                "theme_tags": m.theme_tags,
                "pacing_tags": m.pacing_tags,
                "emotion_tags": m.emotion_tags,
                "director": m.director,
                "vote_average": m.vote_average,
                "popularity_score": m.popularity_score,
            }
            for m in movies
        ]

    async def _upsert_movie(
        self,
        data: dict,
    ) -> Movie:

        result = await self.db.execute(
            select(Movie).where(
                Movie.tmdb_id == data["tmdb_id"]
            )
        )

        movie = result.scalar_one_or_none()

        overview = data.get(
            "overview",
            "",
        )

        keywords = data.get(
            "keywords",
            [],
        )

        genres = data.get(
            "genres",
            [],
        )

        mood_tags = derive_mood_tags(
            genres,
            keywords,
        )

        theme_tags = derive_theme_tags(
            overview,
            keywords,
        )

        tone_tags = derive_tone_tags(
            overview,
            keywords,
        )

        pacing_tags = derive_pacing_tags(
            overview,
            genres,
        )

        emotion_tags = derive_emotion_tags(
            overview,
            keywords,
        )

        release_date = None

        if data.get("release_date"):

            try:

                from datetime import (
                    date as dtdate,
                )

                release_date = (
                    dtdate.fromisoformat(
                        data["release_date"]
                    )
                )

            except (
                ValueError,
                TypeError,
            ):
                pass

        pop_score = compute_popularity_score(
            data.get("vote_average", 0),
            data.get("vote_count", 0),
            release_date,
        )

        if movie is None:

            movie = Movie(
                tmdb_id=data["tmdb_id"],
                title=data["title"],
                original_title=data.get(
                    "original_title"
                ),
                overview=overview,
                tagline=data.get(
                    "tagline"
                ),
                release_date=release_date,
                runtime=data.get(
                    "runtime"
                ),
                original_language=data.get(
                    "original_language"
                ),
                status=data.get(
                    "status"
                ),
                vote_average=data.get(
                    "vote_average",
                    0,
                ),
                vote_count=data.get(
                    "vote_count",
                    0,
                ),
                popularity=data.get(
                    "popularity",
                    0,
                ),
                popularity_score=pop_score,
                poster_path=data.get(
                    "poster_path"
                ),
                backdrop_path=data.get(
                    "backdrop_path"
                ),
                genres=genres,
                crew=data.get(
                    "crew",
                    [],
                ),
                cast=data.get(
                    "cast",
                    [],
                ),
                keywords=keywords,
                mood_tags=mood_tags,
                tone_tags=tone_tags,
                theme_tags=theme_tags,
                pacing_tags=pacing_tags,
                emotion_tags=emotion_tags,
                production_companies=data.get(
                    "production_companies",
                    [],
                ),
                embedding_synced=False,
            )

            self.db.add(movie)

        else:

            movie.vote_average = data.get(
                "vote_average",
                movie.vote_average,
            )

            movie.vote_count = data.get(
                "vote_count",
                movie.vote_count,
            )

            movie.popularity = data.get(
                "popularity",
                movie.popularity,
            )

            movie.popularity_score = (
                pop_score
            )

            movie.mood_tags = mood_tags
            movie.tone_tags = tone_tags
            movie.theme_tags = theme_tags
            movie.pacing_tags = pacing_tags
            movie.emotion_tags = emotion_tags

        await self.db.commit()

        await self.db.refresh(movie)

        return movie

    def _passes_filters(
        self,
        movie: Movie,
        filters: MovieSearchFilters,
    ) -> bool:

        if (
            filters.rating_min
            and movie.vote_average
            < filters.rating_min
        ):
            return False

        if (
            filters.year_min
            and movie.year
            and movie.year
            < filters.year_min
        ):
            return False

        if (
            filters.year_max
            and movie.year
            and movie.year
            > filters.year_max
        ):
            return False

        if (
            filters.language
            and movie.original_language
            != filters.language
        ):
            return False

        if filters.genres:

            if not any(
                g in (movie.genres or [])
                for g in filters.genres
            ):
                return False

        return True

    @staticmethod
    def to_card(
        movie: Movie,
    ) -> MovieCardResponse:

        return MovieCardResponse(
            tmdb_id=movie.tmdb_id,
            title=movie.title,
            poster_url=movie.poster_url,
            backdrop_url=movie.backdrop_url,
            vote_average=movie.vote_average,
            year=movie.year,
            genres=movie.genres or [],
            runtime=movie.runtime,
            popularity_score=movie.popularity_score,
        )

    @staticmethod
    def to_detail(
        movie: Movie,
    ) -> MovieDetailResponse:

        return MovieDetailResponse(
            tmdb_id=movie.tmdb_id,
            title=movie.title,
            overview=movie.overview,
            tagline=movie.tagline,
            release_date=movie.release_date,
            vote_average=movie.vote_average,
            vote_count=movie.vote_count,
            popularity=movie.popularity,
            poster_path=movie.poster_path,
            backdrop_path=movie.backdrop_path,
            poster_url=movie.poster_url,
            backdrop_url=movie.backdrop_url,
            genres=movie.genres or [],
            runtime=movie.runtime,
            original_language=movie.original_language,
            director=movie.director,
            top_cast=movie.top_cast,
            mood_tags=movie.mood_tags or [],
            keywords=movie.keywords or [],
            year=movie.year,
        )