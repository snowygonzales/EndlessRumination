from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import UserDB, get_db
from app.models.schemas import (
    SubscriptionStatusResponse,
    SubscriptionTier,
    VerifyReceiptRequest,
)
from app.services.auth_service import require_user
from app.services.rate_limiter import get_usage
from app.services.receipt_validator import ValidationResult
from app.services.apple_validator import AppleValidator
from app.services.google_validator import GoogleValidator
from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
router = APIRouter(prefix="/api/v1/subscription", tags=["subscription"])

# Product IDs that correspond to voice packs (non-consumable)
PACK_PRODUCT_IDS = {
    "com.endlessrumination.pack.strategists",
    "com.endlessrumination.pack.revolutionaries",
    "com.endlessrumination.pack.philosophers",
    "com.endlessrumination.pack.creators",
}

PRO_SUBSCRIPTION_ID = "com.endlessrumination.pro.monthly"


def _get_apple_validator() -> AppleValidator | None:
    if settings.apple_key_id and settings.apple_private_key_path:
        return AppleValidator(
            key_id=settings.apple_key_id,
            issuer_id=settings.apple_issuer_id,
            private_key_path=settings.apple_private_key_path,
            bundle_id=settings.apple_bundle_id,
        )
    return None


def _get_google_validator() -> GoogleValidator | None:
    if settings.google_play_service_account_json:
        return GoogleValidator(
            service_account_json=settings.google_play_service_account_json,
            package_name=settings.google_play_package_name,
        )
    return None


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
async def verify_receipt(
    payload: VerifyReceiptRequest,
    user: UserDB = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify a purchase receipt and activate entitlements.

    Supports both iOS (App Store Server API v2) and Android
    (Google Play Developer API). Updates user tier and owned packs.
    """
    # Select the right validator
    if payload.platform == "ios":
        validator = _get_apple_validator()
        if validator is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Apple receipt validation not configured",
            )
    elif payload.platform == "android":
        validator = _get_google_validator()
        if validator is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google Play receipt validation not configured",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported platform: {payload.platform}",
        )

    # Validate the receipt
    result: ValidationResult = await validator.validate_purchase(
        product_id=payload.product_id,
        purchase_token=payload.purchase_token,
        is_subscription=payload.is_subscription,
    )

    if not result.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Receipt validation failed: {result.error}",
        )

    # Update user entitlements on the injected user object (same session)
    if payload.product_id == PRO_SUBSCRIPTION_ID:
        user.subscription_tier = "pro"
        if result.expires_at:
            user.subscription_expires = datetime.fromisoformat(result.expires_at)
        logger.info("Activated Pro for user %s", user.id)

    elif payload.product_id in PACK_PRODUCT_IDS:
        current_packs = set(
            p for p in (user.owned_pack_ids or "").split(",") if p
        )
        current_packs.add(payload.product_id)
        user.owned_pack_ids = ",".join(sorted(current_packs))
        logger.info("Added pack %s for user %s", payload.product_id, user.id)

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown product: {payload.product_id}",
        )

    await db.commit()

    return {
        "status": "ok",
        "product_id": payload.product_id,
        "is_subscription": payload.is_subscription,
    }
