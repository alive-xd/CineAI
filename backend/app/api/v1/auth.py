"""
app/api/v1/auth.py
────────────────────
Authentication routes.
Refresh tokens are set as httpOnly cookies — never exposed to JavaScript.
"""

from fastapi import APIRouter, Cookie, Depends, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.exceptions import UnauthorizedException
from app.core.rate_limit import limiter
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

REFRESH_COOKIE = "refresh_token"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth",
    )


@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit("5/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user account.
    """
    service = AuthService(db)
    return await service.register(body)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate and log in a user.
    Sets a refresh token as an httpOnly cookie.
    """
    service = AuthService(db)
    token_response, refresh_token = await service.login(body.email, body.password)
    _set_refresh_cookie(response, refresh_token)
    return token_response


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
    db: AsyncSession = Depends(get_db),
):
    if not refresh_token:
        raise UnauthorizedException("Refresh token missing")

    service = AuthService(db)

    # FIX: refresh() now returns (TokenResponse, new_refresh_token)
    # Set the rotated token back as cookie so next refresh works
    token_response, new_refresh_token = await service.refresh(refresh_token)
    _set_refresh_cookie(response, new_refresh_token)

    return token_response


@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    await service.logout(str(current_user.id))
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)