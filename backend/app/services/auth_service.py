"""
app/services/auth_service.py
──────────────────────────────
Handles user registration, login, and token management.
"""

import logging
from datetime import datetime, UTC

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_refresh_token_expiry,
    hash_password,
    verify_password,
)
from app.config import settings
from app.models.user import User
from app.schemas.auth import RegisterRequest, TokenResponse, UserResponse
import random

logger = logging.getLogger(__name__)


class AuthService:

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(self, request: RegisterRequest) -> UserResponse:
        existing = await self.db.execute(
            select(User).where(User.email == request.email)
        )
        if existing.scalar_one_or_none():
            raise ConflictException("Email already registered")

        existing_username = await self.db.execute(
            select(User).where(User.username == request.username)
        )
        if existing_username.scalar_one_or_none():
            raise ConflictException("Username already taken")

        user = User(
            email=request.email,
            username=request.username,
            hashed_password=hash_password(request.password),
            is_active=True,
            ab_group=random.choice(["control", "variant"]),
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"Registered new user: {user.email}")
        return UserResponse.model_validate(user)

    async def login(self, email: str, password: str) -> tuple[TokenResponse, str]:
        """
        Returns (TokenResponse, refresh_token_string).
        Caller sets refresh_token as httpOnly cookie.
        """
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedException("Account is disabled")

        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"username": user.username},
        )
        refresh_token = create_refresh_token()

        user.refresh_token = refresh_token
        user.refresh_token_expires_at = get_refresh_token_expiry()
        await self.db.commit()

        return (
            TokenResponse(
                access_token=access_token,
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            ),
            refresh_token,
        )

    async def refresh(self, refresh_token: str) -> tuple[TokenResponse, str]:
        """
        Validate refresh token, rotate it, and issue new access token.
        Returns (TokenResponse, new_refresh_token_string).
        Caller MUST update the browser cookie with the new refresh token.
        """
        result = await self.db.execute(
            select(User).where(User.refresh_token == refresh_token)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise UnauthorizedException("Invalid refresh token")

        if user.refresh_token_expires_at < datetime.now(UTC):
            raise UnauthorizedException("Refresh token expired — please log in again")

        # Rotate refresh token
        new_refresh = create_refresh_token()
        user.refresh_token = new_refresh
        user.refresh_token_expires_at = get_refresh_token_expiry()
        await self.db.commit()

        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"username": user.username},
        )

        return (
            TokenResponse(
                access_token=access_token,
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            ),
            new_refresh,
        )

    async def logout(self, user_id: str) -> None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.refresh_token = None
            user.refresh_token_expires_at = None
            await self.db.commit()