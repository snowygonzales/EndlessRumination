from fastapi import APIRouter, Depends, HTTPException, status

from app.models.database import UserDB
from app.models.schemas import (
    SubscriptionStatusResponse,
    SubscriptionTier,
    VerifyReceiptRequest,
)
from app.services.auth_service import require_user
from app.services.rate_limiter import get_usage
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/v1/subscription", tags=["subscription"])


@router.get("/status", response_model=SubscriptionStatusResponse)
async def subscription_status(user: UserDB = Depends(require_user)):
    """Get current subscription status and usage."""
    is_pro = user.subscription_tier == "pro"
    user_id = str(user.id)

    takes_used = await get_usage(user_id, "takes")
    problems_used = await get_usage(user_id, "problems")

    return SubscriptionStatusResponse(
        tier=SubscriptionTier(user.subscription_tier),
        expires_at=user.subscription_expires,
        daily_takes_used=takes_used,
        daily_takes_limit=999999 if is_pro else settings.free_takes_per_day,
        daily_problems_used=problems_used,
        daily_problems_limit=(
            settings.pro_problems_per_day if is_pro else settings.free_problems_per_day
        ),
    )


@router.post("/verify-receipt")
async def verify_receipt(payload: VerifyReceiptRequest):
    """Verify an Apple StoreKit receipt and activate Pro.

    TODO: Implement Apple receipt validation via App Store Server API.
    This is a placeholder for Phase 3 (monetization).
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Receipt verification not yet implemented",
    )
