"""
app/core/security.py
────────────────────
Handles:
  - Password hashing/verification (bcrypt via passlib)
  - JWT access token creation and verification
  - Refresh token generation (opaque, stored in httpOnly cookie)

Design decisions:
  - Access tokens are short-lived (15 min), stateless JWTs.
  - Refresh tokens are 7-day httpOnly cookies for XSS protection.
  - Token payload includes user_id and token_type to prevent type confusion attacks.
"""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.core.exceptions import UnauthorizedException

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


# ── Password ───────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """
    bcrypt only supports first 72 bytes.
    Truncate safely for MVP stability.
    """
    plain = plain[:72]
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Must apply same truncation during verification.
    """
    plain = plain[:72]
    return pwd_context.verify(plain, hashed)


# ── Access Token ───────────────────────────────────────────────────────────────

def create_access_token(
    subject: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Creates a signed JWT access token.

    Args:
        subject: The user's UUID string — stored in the 'sub' claim.
        extra_claims: Optional additional payload (e.g. role, username).

    Returns:
        Encoded JWT string.
    """

    now = datetime.now(UTC)

    expire = now + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "type": "access",
        **(extra_claims or {}),
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decodes and validates a JWT access token.
    Raises UnauthorizedException on any validation failure.
    """

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        if payload.get("type") != "access":
            raise UnauthorizedException("Invalid token type")

        return payload

    except JWTError as exc:
        raise UnauthorizedException(
            "Could not validate credentials"
        ) from exc


# ── Refresh Token ──────────────────────────────────────────────────────────────

def create_refresh_token() -> str:
    """
    Generates a cryptographically secure opaque refresh token.
    This is NOT a JWT — it is stored in the DB against the user record
    and rotated on every refresh cycle.
    """

    return secrets.token_urlsafe(64)


def get_refresh_token_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )