from __future__ import annotations

from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class ValidationResult:
    """Result of receipt/purchase token validation."""

    valid: bool
    product_id: str | None = None
    is_subscription: bool = False
    expires_at: str | None = None  # ISO 8601 for subscriptions
    error: str | None = None


class ReceiptValidator(ABC):
    """Abstract base for platform-specific receipt validators."""

    @abstractmethod
    async def validate_purchase(
        self,
        product_id: str,
        purchase_token: str,
        is_subscription: bool,
    ) -> ValidationResult:
        ...
