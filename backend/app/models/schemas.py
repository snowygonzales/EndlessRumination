from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from enum import Enum


# ── Enums ──────────────────────────────────────────────

class SubscriptionTier(str, Enum):
    free = "free"
    pro = "pro"


# ── Request Models ─────────────────────────────────────

class ProblemInput(BaseModel):
    problem: str = Field(..., min_length=1, max_length=5000)


class GenerateTakeRequest(BaseModel):
    problem: str = Field(..., min_length=1, max_length=5000)
    lens_index: int = Field(..., ge=0, le=19)


class GenerateBatchRequest(BaseModel):
    problem: str = Field(..., min_length=1, max_length=5000)
    lens_indices: list[int] = Field(default_factory=lambda: list(range(20)))


class RegisterRequest(BaseModel):
    device_id: str = Field(..., min_length=1)
    email: str | None = None


class LoginRequest(BaseModel):
    device_id: str = Field(..., min_length=1)


class VerifyReceiptRequest(BaseModel):
    receipt_data: str


# ── Response Models ────────────────────────────────────

class SafetyCheckResponse(BaseModel):
    safe: bool
    category: str | None = None
    resources: list[dict] | None = None


class TakeResponse(BaseModel):
    lens_index: int
    headline: str
    body: str


class TakeStreamEvent(BaseModel):
    lens_index: int
    headline: str
    body: str


class UserResponse(BaseModel):
    id: UUID
    device_id: str
    email: str | None
    subscription_tier: SubscriptionTier
    daily_takes_used: int
    created_at: datetime


class AuthResponse(BaseModel):
    token: str
    user: UserResponse


class SubscriptionStatusResponse(BaseModel):
    tier: SubscriptionTier
    expires_at: datetime | None = None
    daily_takes_used: int
    daily_takes_limit: int
    daily_problems_used: int
    daily_problems_limit: int


class ProblemHistoryItem(BaseModel):
    id: UUID
    text: str
    created_at: datetime
    takes: list[TakeResponse]


class HistoryResponse(BaseModel):
    problems: list[ProblemHistoryItem]


CRISIS_RESOURCES = [
    {
        "name": "988 Suicide & Crisis Lifeline",
        "action": "call",
        "value": "988",
        "description": "Free, confidential, 24/7 support",
    },
    {
        "name": "Crisis Text Line",
        "action": "text",
        "value": "HOME to 741741",
        "description": "Text-based crisis counseling",
    },
]
