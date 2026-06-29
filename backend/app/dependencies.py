"""
app/dependencies.py
─────────────────────
Shared FastAPI dependencies injected into route handlers.
"""

from fastapi import Depends, Cookie
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedException
from app.models.user import User
import uuid

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extracts the JWT from the Authorization header, decodes it,
    and returns the authenticated User ORM object.
    Raises 401 if token is missing, invalid, or the user doesn't exist.
    """
    if not credentials:
        raise UnauthorizedException("Authorization header missing")

    payload = decode_access_token(credentials.credentials)
    user_id: str | None = payload.get("sub")

    if not user_id:
        raise UnauthorizedException("Invalid token payload")

    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise UnauthorizedException("Invalid token payload")
    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise UnauthorizedException("User not found or inactive")

    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Same as get_current_user but returns None instead of raising 401.
    Used for routes that show different content for authenticated vs anonymous users.
    """
    if not credentials:
        return None
    try:
        return await get_current_user(credentials, db)
    except Exception:
        return None
