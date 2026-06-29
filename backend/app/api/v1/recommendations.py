"""
app/api/v1/recommendations.py
───────────────────────────────
Recommendation endpoints:
  GET  /recommendations              — personalised homepage recs
  POST /recommendations/feedback     — submit feedback (liked/dismissed)
  POST /recommendations/refresh      — force cache invalidation + recompute
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.all_models import RecommendationFeedback
from app.schemas import FeedbackRequest, RecommendationResponse
from app.services.recommendation_service import RecommendationService
from app.ml.feedback.weight_updater import process_feedback
from app.ml.embeddings.user_profile import update_user_profile

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("", response_model=list[RecommendationResponse])
async def get_recommendations(
    top_k: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Personalised hybrid recommendations for the authenticated user.
    Served from Redis cache (TTL 1hr) unless force-refreshed.
    Cold-start users (< 5 ratings) receive an empty list with a prompt
    to rate movies.
    """
    service = RecommendationService(db)
    return await service.get_recommendations(str(current_user.id), top_k=top_k)


@router.post("/feedback", status_code=204)
async def submit_feedback(
    body: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Record user feedback on a recommendation.

    Actions:
      liked       — strong positive signal; increases dominant signal's weight
      dismissed   — negative signal; decreases dominant signal's weight
      clicked     — weak positive (opened movie detail)
      watchlisted — medium positive (added to watchlist from rec card)

    Side effects:
      - Updates UserPreference.hybrid_weights (adaptive ranker)
      - Invalidates recommendation cache for this user
    """
    feedback = RecommendationFeedback(
        user_id=current_user.id,
        recommendation_id=body.recommendation_id,
        action=body.action,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)

    # Update adaptive weights
    await process_feedback(feedback, db)

    # Invalidate cache so next request gets fresh recs
    service = RecommendationService(db)
    await service.invalidate_cache(str(current_user.id))


@router.post("/refresh", response_model=list[RecommendationResponse])
async def refresh_recommendations(
    top_k: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Force-refresh recommendations, bypassing cache.
    Also triggers a user profile embedding update.
    Called after significant interactions (multiple ratings, watchlist adds).
    """
    # Recompute user taste profile first
    await update_user_profile(str(current_user.id), db)

    service = RecommendationService(db)
    return await service.get_recommendations(
        str(current_user.id),
        top_k=top_k,
        force_refresh=True,
    )
