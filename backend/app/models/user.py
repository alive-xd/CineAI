"""
app/models/user.py
──────────────────
Users table. Stores credentials, refresh token (for rotation), and account status.
Relationships are lazy by default — load explicitly with selectinload() in queries.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ab_group: Mapped[str] = mapped_column(String(20), default="control", nullable=False)

    # Refresh token rotation — store current valid refresh token hash
    refresh_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    refresh_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    ratings: Mapped[list["Rating"]] = relationship(  # noqa: F821
        "Rating", back_populates="user", lazy="noload"
    )
    watchlist: Mapped[list["Watchlist"]] = relationship(  # noqa: F821
        "Watchlist", back_populates="user", lazy="noload"
    )
    reviews: Mapped[list["Review"]] = relationship(  # noqa: F821
        "Review", back_populates="user", lazy="noload"
    )
    preferences: Mapped["UserPreference | None"] = relationship(  # noqa: F821
        "UserPreference", back_populates="user", uselist=False, lazy="noload"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(  # noqa: F821
        "Recommendation", back_populates="user", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"
