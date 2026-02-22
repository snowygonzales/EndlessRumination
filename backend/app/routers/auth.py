from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import UserDB, get_db
from app.models.schemas import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    SubscriptionTier,
    UserResponse,
)
from app.services.auth_service import create_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _user_response(user: UserDB) -> UserResponse:
    return UserResponse(
        id=user.id,
        device_id=user.device_id,
        email=user.email,
        subscription_tier=SubscriptionTier(user.subscription_tier),
        daily_takes_used=user.daily_takes_used,
        created_at=user.created_at,
    )


@router.post("/register", response_model=AuthResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user by device ID. Returns JWT token."""
    # Check if device already registered
    result = await db.execute(
        select(UserDB).where(UserDB.device_id == payload.device_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device already registered. Use /login instead.",
        )

    user = UserDB(device_id=payload.device_id, email=payload.email)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_token(user.id)
    return AuthResponse(token=token, user=_user_response(user))


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login by device ID. Returns JWT token."""
    result = await db.execute(
        select(UserDB).where(UserDB.device_id == payload.device_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not registered. Use /register first.",
        )

    token = create_token(user.id)
    return AuthResponse(token=token, user=_user_response(user))
