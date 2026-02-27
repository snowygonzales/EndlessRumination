from __future__ import annotations

import time
import json
import base64
import logging

import httpx
import jwt
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from app.services.receipt_validator import ReceiptValidator, ValidationResult

logger = logging.getLogger(__name__)

# Apple App Store Server API v2 endpoints
APPLE_PRODUCTION_URL = "https://api.storekit.itunes.apple.com"
APPLE_SANDBOX_URL = "https://api.storekit-sandbox.itunes.apple.com"


class AppleValidator(ReceiptValidator):
    """Validates iOS purchases via App Store Server API v2.

    Uses JWT authentication with a .p8 key from App Store Connect.
    Decodes the JWS-signed transaction to extract product/expiry info.
    """

    def __init__(
        self,
        key_id: str,
        issuer_id: str,
        private_key_path: str,
        bundle_id: str,
    ):
        self.key_id = key_id
        self.issuer_id = issuer_id
        self.bundle_id = bundle_id
        self._private_key_path = private_key_path
        self._private_key = None

    def _load_key(self):
        if self._private_key is None:
            with open(self._private_key_path, "rb") as f:
                self._private_key = load_pem_private_key(f.read(), password=None)
        return self._private_key

    def _create_api_token(self) -> str:
        """Create a JWT for App Store Server API authentication."""
        now = int(time.time())
        payload = {
            "iss": self.issuer_id,
            "iat": now,
            "exp": now + 3600,  # 1 hour
            "aud": "appstoreconnect-v1",
            "bid": self.bundle_id,
        }
        return jwt.encode(
            payload,
            self._load_key(),
            algorithm="ES256",
            headers={"kid": self.key_id},
        )

    def _decode_jws_payload(self, jws_token: str) -> dict:
        """Decode the payload from an Apple JWS signed transaction.

        Apple signs transactions as JWS (JSON Web Signature).
        We decode the payload segment (base64url) without verifying
        Apple's signature here — the fact that the API returned it
        is sufficient proof of authenticity.
        """
        parts = jws_token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWS format")

        # Base64url decode the payload (2nd segment)
        payload_b64 = parts[1]
        # Add padding if needed
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding

        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        return json.loads(payload_bytes)

    async def validate_purchase(
        self,
        product_id: str,
        purchase_token: str,
        is_subscription: bool,
    ) -> ValidationResult:
        """Validate an iOS purchase using the transaction ID.

        For iOS, `purchase_token` is the transaction ID (original_transaction_id).
        We call the App Store Server API to get the signed transaction info.
        """
        if not self.key_id or not self.issuer_id or not self._private_key_path:
            return ValidationResult(
                valid=False,
                error="Apple API credentials not configured",
            )

        token = self._create_api_token()
        headers = {"Authorization": f"Bearer {token}"}

        # Try production first, then sandbox
        for base_url in [APPLE_PRODUCTION_URL, APPLE_SANDBOX_URL]:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{base_url}/inApps/v1/transactions/{purchase_token}",
                        headers=headers,
                        timeout=15.0,
                    )

                if response.status_code == 200:
                    data = response.json()
                    signed_transaction = data.get("signedTransactionInfo")
                    if not signed_transaction:
                        continue

                    tx_info = self._decode_jws_payload(signed_transaction)
                    tx_product = tx_info.get("productId")

                    if tx_product != product_id:
                        return ValidationResult(
                            valid=False,
                            product_id=tx_product,
                            error=f"Product mismatch: expected {product_id}, got {tx_product}",
                        )

                    expires_at = None
                    if is_subscription:
                        expires_ms = tx_info.get("expiresDate")
                        if expires_ms:
                            from datetime import datetime, timezone

                            expires_at = datetime.fromtimestamp(
                                expires_ms / 1000, tz=timezone.utc
                            ).isoformat()

                    return ValidationResult(
                        valid=True,
                        product_id=tx_product,
                        is_subscription=is_subscription,
                        expires_at=expires_at,
                    )

                elif response.status_code == 404:
                    # Transaction not found at this endpoint, try next
                    continue
                else:
                    logger.warning(
                        "Apple API returned %d: %s",
                        response.status_code,
                        response.text,
                    )
                    continue

            except Exception as e:
                logger.error("Apple validation error: %s", e)
                continue

        return ValidationResult(
            valid=False,
            error="Transaction not found on Apple servers",
        )
