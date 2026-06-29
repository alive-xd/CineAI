"""
app/api/v1/router.py
──────────────────────
Aggregates all v1 route modules into a single APIRouter.
Mounted at /api/v1 in main.py.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.movies import router as movies_router
from app.api.v1.search import router as search_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.interactions import (
    ratings_router,
    watchlist_router,
    profile_router,
)

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(movies_router)
api_router.include_router(search_router)
api_router.include_router(recommendations_router)
api_router.include_router(ratings_router)
api_router.include_router(watchlist_router)
api_router.include_router(profile_router)
