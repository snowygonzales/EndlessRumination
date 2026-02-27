from __future__ import annotations

import json
import logging

from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.services.receipt_validator import ReceiptValidator, ValidationResult

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/androidpublisher"]


class GoogleValidator(ReceiptValidator):
    """Validates Android purchases via Google Play Developer API.

    Uses a service account for authentication.
    Calls purchases.subscriptionsv2.get for subs, purchases.products.get for one-time.
    """

    def __init__(self, service_account_json: str, package_name: str):
        self.package_name = package_name
        self._service_account_json = service_account_json
        self._service = None

    def _get_service(self):
        if self._service is None:
            info = json.loads(self._service_account_json)
            credentials = service_account.Credentials.from_service_account_info(
                info, scopes=SCOPES
            )
            self._service = build(
                "androidpublisher", "v3", credentials=credentials, cache_discovery=False
            )
        return self._service

    async def validate_purchase(
        self,
        product_id: str,
        purchase_token: str,
        is_subscription: bool,
    ) -> ValidationResult:
        """Validate an Android purchase using the purchase token."""
        if not self._service_account_json:
            return ValidationResult(
                valid=False,
                error="Google Play API credentials not configured",
            )

        try:
            service = self._get_service()

            if is_subscription:
                return await self._validate_subscription(
                    service, product_id, purchase_token
                )
            else:
                return await self._validate_product(
                    service, product_id, purchase_token
                )

        except Exception as e:
            logger.error("Google Play validation error: %s", e)
            return ValidationResult(
                valid=False,
                error=f"Google Play API error: {str(e)}",
            )

    async def _validate_subscription(
        self, service, product_id: str, purchase_token: str
    ) -> ValidationResult:
        """Validate a subscription using subscriptionsv2.get (v3 API)."""
        try:
            result = (
                service.purchases()
                .subscriptionsv2()
                .get(
                    packageName=self.package_name,
                    token=purchase_token,
                )
                .execute()
            )

            # subscriptionsv2.get returns subscription state
            subscription_state = result.get("subscriptionState", "")

            if subscription_state in (
                "SUBSCRIPTION_STATE_ACTIVE",
                "SUBSCRIPTION_STATE_IN_GRACE_PERIOD",
            ):
                # Extract expiry from lineItems
                expires_at = None
                line_items = result.get("lineItems", [])
                if line_items:
                    expiry_time = line_items[0].get("expiryTime")
                    if expiry_time:
                        expires_at = expiry_time

                return ValidationResult(
                    valid=True,
                    product_id=product_id,
                    is_subscription=True,
                    expires_at=expires_at,
                )
            else:
                return ValidationResult(
                    valid=False,
                    product_id=product_id,
                    is_subscription=True,
                    error=f"Subscription not active: {subscription_state}",
                )

        except Exception as e:
            logger.error("Google subscription validation error: %s", e)
            return ValidationResult(
                valid=False,
                error=f"Subscription validation failed: {str(e)}",
            )

    async def _validate_product(
        self, service, product_id: str, purchase_token: str
    ) -> ValidationResult:
        """Validate a one-time purchase using purchases.products.get."""
        try:
            result = (
                service.purchases()
                .products()
                .get(
                    packageName=self.package_name,
                    productId=product_id,
                    token=purchase_token,
                )
                .execute()
            )

            # 0 = purchased, 1 = cancelled
            purchase_state = result.get("purchaseState", -1)
            # 1 = acknowledged
            acknowledgement_state = result.get("acknowledgementState", 0)

            if purchase_state == 0:
                return ValidationResult(
                    valid=True,
                    product_id=product_id,
                    is_subscription=False,
                )
            else:
                return ValidationResult(
                    valid=False,
                    product_id=product_id,
                    is_subscription=False,
                    error=f"Purchase not valid: state={purchase_state}",
                )

        except Exception as e:
            logger.error("Google product validation error: %s", e)
            return ValidationResult(
                valid=False,
                error=f"Product validation failed: {str(e)}",
            )
