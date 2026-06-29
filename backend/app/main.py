"""
app/main.py
─────────────
FastAPI application factory.

Lifespan:
  - Initialises Redis, Qdrant on startup
  - Trains CF model from DB ratings on startup
  - Schedules background workers (APScheduler)
  - Gracefully closes connections on shutdown

Middleware:
  - CORS for frontend domains
  - Structured request logging
  - GZip compression for large responses
"""

import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.config import settings
from app.core.exceptions import CineAIException
from app.core.redis_client import close_redis, init_redis
from app.integrations.qdrant_client import close_qdrant, init_qdrant
from app.core.rate_limit import limiter

# ── Structured logging setup ───────────────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger()


# ── Lifespan ───────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Starting CineAI backend", env=settings.ENVIRONMENT)

    # Redis
    await init_redis()

    # Qdrant
    await init_qdrant()

    # Train CF model from DB ratings
    # Fast (~1s) — no disk dependency, works immediately
    from app.workers.scheduler import start_scheduler, train_cf_on_startup
    await train_cf_on_startup()

    # Start background scheduler
    start_scheduler()

    logger.info("CineAI startup complete")
    yield

    # Shutdown
    logger.info("Shutting down CineAI")
    from app.workers.scheduler import stop_scheduler
    stop_scheduler()
    await close_redis()
    await close_qdrant()


# ── App factory ────────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-powered movie recommendation platform",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    @app.exception_handler(CineAIException)
    async def cineai_exception_handler(request: Request, exc: CineAIException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "error_code": exc.error_code},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error_code": "INTERNAL_ERROR"},
        )

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/health", tags=["Health"])
    async def health():
        return {"status": "ok", "version": settings.APP_VERSION}

    return app


app = create_app()