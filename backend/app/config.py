"""
app/config.py
─────────────
Single source of truth for all configuration.
All values are read from environment variables (with sensible defaults for dev).
Production values come from Render/Railway environment variable dashboard.
"""

from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Application ────────────────────────────────────────────────────────────
    APP_NAME: str = "CineAI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # ── Security ───────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-this-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Database ───────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/cineai"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ── Redis ──────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_TTL_SECONDS: int = 3600
    TRENDING_CACHE_TTL: int = 1800

    # ── Qdrant ─────────────────────────────────────────────────────────────────
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION_MOVIES: str = "movies"
    QDRANT_COLLECTION_USERS: str = "user_profiles"
    VECTOR_DIMENSION: int = 384

    # ── TMDb ───────────────────────────────────────────────────────────────────
    TMDB_API_KEY: str = ""
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
    TMDB_IMAGE_BASE: str = "https://image.tmdb.org/t/p"
    TMDB_REQUEST_TIMEOUT: int = 10

    # ── ML ─────────────────────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_BATCH_SIZE: int = 64
    VECTOR_SEARCH_TOP_K: int = 50
    RECOMMENDATION_TOP_K: int = 20

    # ── Hybrid Ranker Default Weights ──────────────────────────────────────────
    # FIX: semantic raised 0.35→0.50, collab lowered 0.25→0.15,
    # popularity lowered 0.10→0.05. Semantic is the strongest
    # personalization signal; collab is sparse for most users.
    WEIGHT_SEMANTIC: float = 0.50
    WEIGHT_CONTENT: float = 0.30
    WEIGHT_COLLABORATIVE: float = 0.15
    WEIGHT_POPULARITY: float = 0.05

    # ── CORS ───────────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://cineai.vercel.app",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def qdrant_url(self) -> str:
        return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()