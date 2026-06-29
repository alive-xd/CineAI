"""
app/ml/feedback/weight_updater.py
────────────────────────────────────
Updates per-user hybrid ranker weights based on recommendation feedback.

Feedback → Weight update logic:
  Action      | dominant_signal | Effect
  ──────────────────────────────────────────────────────────────────
  liked       | semantic        | ↑ semantic weight slightly
  liked       | content         | ↑ content weight slightly
  liked       | collaborative   | ↑ collab weight slightly
  dismissed   | any             | ↓ that signal's weight slightly
  watchlisted | any             | smaller ↑ (weaker signal than liked)
  clicked     | any             | tiny ↑ (weakest signal)

Update rule: Exponential Moving Average (EMA)
  new_weight = (1 - lr) * old_weight + lr * target_weight
  where lr (learning rate) scales by action strength.

Constraints:
  - Weights always sum to 1.0 (re-normalised after each update)
  - Each weight stays in [0.05, 0.70] — prevents one signal dominating completely
  - Updates are applied incrementally; no full recompute needed

This approach is simple, explainable, and avoids storing a training pipeline
per user. At scale (>10K users), switch to bandit-based contextual learning.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.all_models import Recommendation, RecommendationFeedback, UserPreference

logger = logging.getLogger(__name__)

# How much each action shifts the weights
ACTION_LEARNING_RATES = {
    "liked": 0.08,
    "watchlisted": 0.04,
    "clicked": 0.02,
    "dismissed": 0.06,  # Negative signal — handled separately
}

# Signal weight bounds
WEIGHT_MIN = 0.05
WEIGHT_MAX = 0.70

# Default weights (used if user has no preference record yet)
DEFAULT_WEIGHTS = {
    "semantic": 0.35,
    "content": 0.30,
    "collaborative": 0.25,
    "popularity": 0.10,
}


async def process_feedback(
    feedback: RecommendationFeedback,
    db: AsyncSession,
) -> None:
    """
    Process a single feedback action and update the user's hybrid weights.

    Args:
        feedback: RecommendationFeedback ORM object (already saved to DB).
        db: Async DB session.
    """
    # Load the recommendation to get dominant signal
    rec_result = await db.execute(
        select(Recommendation).where(Recommendation.id == feedback.recommendation_id)
    )
    rec = rec_result.scalar_one_or_none()

    if rec is None:
        return

    dominant_signal = (rec.explanation or {}).get("dominant_signal", "content")
    action = feedback.action
    user_id = str(feedback.user_id)

    # Load or create user preferences
    pref_result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    pref = pref_result.scalar_one_or_none()

    if pref is None:
        pref = UserPreference(user_id=user_id, hybrid_weights=DEFAULT_WEIGHTS.copy())
        db.add(pref)

    current_weights: dict[str, float] = dict(pref.hybrid_weights or DEFAULT_WEIGHTS)

    # Apply weight update
    updated_weights = _update_weights(
        weights=current_weights,
        signal=dominant_signal,
        action=action,
    )

    pref.hybrid_weights = updated_weights
    await db.commit()

    logger.debug(
        f"Updated weights for user {user_id}: "
        f"{action} on {dominant_signal} → {updated_weights}"
    )


def _update_weights(
    weights: dict[str, float],
    signal: str,
    action: str,
) -> dict[str, float]:
    """
    Apply EMA weight update and re-normalise.

    For positive actions: increase target signal weight, EMA toward higher value.
    For 'dismissed': decrease target signal weight, EMA toward lower value.
    """
    if signal not in weights:
        signal = "content"  # Fallback

    lr = ACTION_LEARNING_RATES.get(action, 0.02)
    new_weights = weights.copy()

    if action == "dismissed":
        # Decrease the dominant signal weight
        new_weights[signal] = max(
            WEIGHT_MIN,
            new_weights[signal] - lr * new_weights[signal],
        )
    else:
        # Increase the dominant signal weight using EMA
        target = min(WEIGHT_MAX, new_weights[signal] + lr)
        new_weights[signal] = (1 - lr) * new_weights[signal] + lr * target

    # Re-normalise so weights sum to 1.0
    total = sum(new_weights.values())
    new_weights = {k: round(v / total, 4) for k, v in new_weights.items()}

    # Enforce bounds
    new_weights = {
        k: max(WEIGHT_MIN, min(WEIGHT_MAX, v))
        for k, v in new_weights.items()
    }

    # Final re-normalise after bound clipping
    total = sum(new_weights.values())
    new_weights = {k: round(v / total, 4) for k, v in new_weights.items()}

    return new_weights
