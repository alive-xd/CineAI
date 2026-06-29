"""
app/api/v1/interactions.py
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundException, ConflictException
from app.dependencies import get_current_user
from app.ml.embeddings.user_profile import update_user_profile
from app.models.all_models import Rating, UserPreference, Watchlist
from app.models.movie import Movie
from app.models.user import User
from app.schemas import (
    RatingRequest, RatingResponse,
    WatchlistAddRequest, WatchlistUpdateRequest, WatchlistResponse,
    TasteProfileResponse,
)
from app.services.movie_service import MovieService
from app.services.recommendation_service import RecommendationService
from app.integrations.tmdb_client import TMDbClient

# ══════════════════════════════════════════════════════════════════════════════
# Ratings Router
# ══════════════════════════════════════════════════════════════════════════════
ratings_router = APIRouter(prefix="/ratings", tags=["Ratings"])


@ratings_router.post("", response_model=RatingResponse, status_code=201)
async def rate_movie(
    body: RatingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = MovieService(db, TMDbClient())
    await service.get_or_fetch_movie(body.movie_id)

    result = await db.execute(
        select(Rating).where(
            Rating.user_id == current_user.id,
            Rating.movie_id == body.movie_id,
        )
    )
    rating = result.scalar_one_or_none()

    if rating:
        rating.score = body.score
    else:
        rating = Rating(
            user_id=current_user.id,
            movie_id=body.movie_id,
            score=body.score,
        )
        db.add(rating)

    await db.commit()
    await db.refresh(rating)

    await update_user_profile(str(current_user.id), db)
    rec_service = RecommendationService(db)
    await rec_service.invalidate_cache(str(current_user.id))

    return RatingResponse.model_validate(rating)


@ratings_router.get("/me", response_model=list[RatingResponse])
async def get_my_ratings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Rating)
        .where(Rating.user_id == current_user.id)
        .order_by(Rating.created_at.desc())
    )
    return [RatingResponse.model_validate(r) for r in result.scalars().all()]


# IMPORTANT: /reset MUST be defined BEFORE /{movie_id}
# If /{movie_id} comes first, FastAPI tries to cast "reset" as int and crashes.
@ratings_router.delete("/reset", status_code=204)
async def reset_all_ratings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete ALL ratings + preferences for the current user.
    Rebuilds empty profile after reset so taste endpoint returns
    clean cold-start state instead of stale data.
    """
    try:
        await db.execute(
            delete(Rating).where(Rating.user_id == current_user.id)
        )
        await db.execute(
            delete(UserPreference).where(UserPreference.user_id == current_user.id)
        )
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    # Rebuild empty profile — clears stale taste data immediately
    await update_user_profile(str(current_user.id), db)

    rec_service = RecommendationService(db)
    await rec_service.invalidate_cache(str(current_user.id))


@ratings_router.delete("/{movie_id}", status_code=204)
async def delete_rating(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await db.execute(
        delete(Rating).where(
            Rating.user_id == current_user.id,
            Rating.movie_id == movie_id,
        )
    )
    await db.commit()
    await update_user_profile(str(current_user.id), db)
    rec_service = RecommendationService(db)
    await rec_service.invalidate_cache(str(current_user.id))


# ══════════════════════════════════════════════════════════════════════════════
# Watchlist Router
# ══════════════════════════════════════════════════════════════════════════════
watchlist_router = APIRouter(prefix="/watchlist", tags=["Watchlist"])


@watchlist_router.get("", response_model=list[WatchlistResponse])
async def get_watchlist(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Watchlist, Movie)
        .join(Movie, Watchlist.movie_id == Movie.tmdb_id)
        .where(Watchlist.user_id == current_user.id)
        .order_by(Watchlist.added_at.desc())
    )
    rows = result.all()
    return [
        WatchlistResponse(
            id=wl.id,
            movie=MovieService.to_card(movie),
            watched=wl.watched,
            added_at=wl.added_at,
        )
        for wl, movie in rows
    ]


@watchlist_router.post("", response_model=WatchlistResponse, status_code=201)
async def add_to_watchlist(
    body: WatchlistAddRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = await db.execute(
        select(Watchlist).where(
            Watchlist.user_id == current_user.id,
            Watchlist.movie_id == body.movie_id,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictException("Movie already in watchlist")

    movie_service = MovieService(db, TMDbClient())
    movie = await movie_service.get_or_fetch_movie(body.movie_id)

    wl = Watchlist(user_id=current_user.id, movie_id=body.movie_id)
    db.add(wl)
    await db.commit()
    await db.refresh(wl)

    return WatchlistResponse(
        id=wl.id,
        movie=MovieService.to_card(movie),
        watched=wl.watched,
        added_at=wl.added_at,
    )


@watchlist_router.patch("/{movie_id}", status_code=204)
async def update_watchlist_item(
    movie_id: int,
    body: WatchlistUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Watchlist).where(
            Watchlist.user_id == current_user.id,
            Watchlist.movie_id == movie_id,
        )
    )
    wl = result.scalar_one_or_none()
    if not wl:
        raise NotFoundException("Movie not in watchlist")
    wl.watched = body.watched
    await db.commit()


@watchlist_router.delete("/{movie_id}", status_code=204)
async def remove_from_watchlist(
    movie_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await db.execute(
        delete(Watchlist).where(
            Watchlist.user_id == current_user.id,
            Watchlist.movie_id == movie_id,
        )
    )
    await db.commit()


# ══════════════════════════════════════════════════════════════════════════════
# Profile Router
# ══════════════════════════════════════════════════════════════════════════════
profile_router = APIRouter(prefix="/profile", tags=["Profile"])


@profile_router.get("/taste", response_model=TasteProfileResponse)
async def get_taste_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    pref = result.scalar_one_or_none()

    if not pref:
        return TasteProfileResponse(
            user_id=current_user.id,
            genre_weights={},
            director_affinities={},
            mood_tag_weights={},
            hybrid_weights={
                "semantic": 0.35, "content": 0.30,
                "collaborative": 0.25, "popularity": 0.10,
            },
            total_ratings=0,
            top_genres=[],
            top_directors=[],
            has_enough_data=False,
        )

    top_genres = list(pref.genre_weights.keys())[:5]
    top_directors = list(pref.director_affinities.keys())[:3]

    return TasteProfileResponse(
        user_id=current_user.id,
        genre_weights=pref.genre_weights,
        director_affinities=pref.director_affinities,
        mood_tag_weights=pref.mood_tag_weights,
        hybrid_weights=pref.hybrid_weights,
        total_ratings=pref.total_ratings,
        top_genres=top_genres,
        top_directors=top_directors,
        has_enough_data=pref.total_ratings >= 5,
    )


@profile_router.post("/taste/refresh", status_code=204)
async def refresh_taste_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await update_user_profile(str(current_user.id), db)
