"""
app/core/database.py
────────────────────
Async SQLAlchemy setup.
- Uses asyncpg driver for non-blocking Postgres queries.
- get_db() is a FastAPI dependency that yields a session per request
  and guarantees commit/rollback/close lifecycle.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


# ── Engine ─────────────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,           # Log SQL in development only
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,            # Reconnect on stale connections
)

# ── Session factory ────────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,        # Prevent lazy-load errors after commit
    autocommit=False,
    autoflush=False,
)


# ── Base model ─────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """
    All SQLAlchemy ORM models inherit from this.
    DeclarativeBase (SQLAlchemy 2.x) replaces the old declarative_base() call.
    """
    pass


# ── Dependency ─────────────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency. Injects an async DB session into route handlers.
    Rolls back on exception, always closes the session.

    Usage:
        @router.get("/")
        async def my_route(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
