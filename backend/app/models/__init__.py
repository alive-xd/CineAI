# Import all models so Alembic can discover them for autogenerate
from app.models.user import User
from app.models.movie import Movie
from app.models.all_models import (
    Rating,
    Watchlist,
    Review,
    UserPreference,
    MovieEmbedding,
    Recommendation,
    RecommendationFeedback,
)

__all__ = [
    "User",
    "Movie",
    "Rating",
    "Watchlist",
    "Review",
    "UserPreference",
    "MovieEmbedding",
    "Recommendation",
    "RecommendationFeedback",
]
