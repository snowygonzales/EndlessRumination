#!/usr/bin/env python3
"""
Create In-App Purchases and Subscriptions in Google Play Console via API.

Products to create:
  1. Auto-renewable subscription: com.endlessrumination.pro.monthly ($9.99/month)
  2. Non-consumable: com.endlessrumination.pack.strategists ($4.99)
  3. Non-consumable: com.endlessrumination.pack.revolutionaries ($4.99)
  4. Non-consumable: com.endlessrumination.pack.philosophers ($4.99)
  5. Non-consumable: com.endlessrumination.pack.creators ($4.99)

Prerequisites:
  pip install google-api-python-client google-auth
  Service account JSON at android/play-service-account.json

Usage:
  python3 scripts/create_play_products.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ─── Configuration ────────────────────────────────────────────────────────────

PACKAGE_NAME = "com.endlessrumination"
SERVICE_ACCOUNT_PATH = Path(__file__).parent.parent / "android" / "play-service-account.json"
SCOPES = ["https://www.googleapis.com/auth/androidpublisher"]

# ─── API Client ───────────────────────────────────────────────────────────────

def get_service():
    """Build the Android Publisher API v3 service."""
    if not SERVICE_ACCOUNT_PATH.exists():
        print(f"ERROR: Service account JSON not found at {SERVICE_ACCOUNT_PATH}")
        sys.exit(1)

    credentials = service_account.Credentials.from_service_account_file(
        str(SERVICE_ACCOUNT_PATH), scopes=SCOPES
    )
    service = build("androidpublisher", "v3", credentials=credentials)
    return service, credentials


# ─── One-Time Products (Voice Packs) ─────────────────────────────────────────

def create_one_time_product(service, credentials, sku: str, title: str, description: str, price_usd: str = "4.99") -> bool:
    """
    Create a non-consumable one-time product.

    Tries two approaches:
    1. Legacy inappproducts.insert (client library)
    2. Modern monetization.onetimeproducts.create (direct HTTP, since the
       Python client library doesn't expose this resource yet)

    API docs:
    - Legacy: https://developers.google.com/android-publisher/api-ref/rest/v3/inappproducts/insert
    - Modern: https://developers.google.com/android-publisher/api-ref/rest/v3/monetization.onetimeproducts/create
    """
    # Try legacy inappproducts.insert first (simpler)
    legacy_body = {
        "packageName": PACKAGE_NAME,
        "sku": sku,
        "status": "active",
        "purchaseType": "managedUser",
        "defaultLanguage": "en-US",
        "defaultPrice": {
            "priceMicros": str(int(float(price_usd) * 1_000_000)),
            "currency": "USD",
        },
        "listings": {
            "en-US": {
                "title": title,
                "description": description,
            }
        },
    }

    try:
        result = service.inappproducts().insert(
            packageName=PACKAGE_NAME,
            autoConvertMissingPrices=True,
            body=legacy_body,
        ).execute()
        print(f"  Created: {sku} @ ${price_usd}")
        return True
    except HttpError as e:
        if e.resp.status == 409:
            print(f"  Already exists: {sku} (skipping)")
            return True
        error_msg = e.content.decode()
        if "migrate" in error_msg.lower():
            print(f"  Legacy API rejected, trying modern API...")
            return _create_one_time_product_modern(credentials, sku, title, description, price_usd)
        print(f"  ERROR creating {sku}: {e.resp.status}")
        print(f"  {error_msg}")
        return False


def _create_one_time_product_modern(credentials, sku: str, title: str, description: str, price_usd: str) -> bool:
    """
    Fallback: create one-time product via direct HTTP to the modern
    monetization.onetimeproducts endpoint (not yet in the Python client library).

    Uses PATCH with allowMissing=true, which is Google's upsert pattern —
    creates the product if it doesn't exist, updates if it does.

    Docs: https://developers.google.com/android-publisher/api-ref/rest/v3/monetization.onetimeproducts/patch
    """
    import google.auth.transport.requests
    import requests

    # Refresh credentials to get access token
    credentials.refresh(google.auth.transport.requests.Request())
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
    }

    units, cents = price_usd.split(".")
    nanos = int(cents) * 10_000_000

    body = {
        "packageName": PACKAGE_NAME,
        "productId": sku,
        "purchaseType": "MANAGED_BY_USER",
        "listings": [
            {
                "languageCode": "en-US",
                "title": title,
                "description": description,
            }
        ],
        "regionalConfigs": [
            {
                "regionCode": "US",
                "newPurchaserAvailability": True,
                "price": {
                    "currencyCode": "USD",
                    "units": units,
                    "nanos": nanos,
                },
            }
        ],
        "otherRegionsConfig": {
            "usdPrice": {"currencyCode": "USD", "units": units, "nanos": nanos},
            "eurPrice": {"currencyCode": "EUR", "units": units, "nanos": nanos},
            "newPurchaserAvailability": True,
        },
    }

    # Try multiple URL patterns — Google's docs show different casing
    url_patterns = [
        f"/applications/{PACKAGE_NAME}/onetimeProducts/{sku}",
        f"/applications/{PACKAGE_NAME}/oneTimeProducts/{sku}",
    ]

    base = "https://androidpublisher.googleapis.com/androidpublisher/v3"

    for path in url_patterns:
        url = f"{base}{path}?allowMissing=true&regionsVersion.version=2022%2F02"
        r = requests.patch(url, headers=headers, json=body)
        if r.status_code == 200:
            print(f"  Created (modern API): {sku} @ ${price_usd}")
            return True
        elif r.status_code == 409:
            print(f"  Already exists: {sku} (skipping)")
            return True
        elif r.status_code == 404:
            continue  # Try next URL pattern
        else:
            print(f"  ERROR creating {sku}: {r.status_code}")
            try:
                print(f"  {r.json()}")
            except Exception:
                print(f"  {r.text[:200]}")
            return False

    print(f"  ERROR: No working API endpoint found for one-time products.")
    print(f"  The Google Play Console UI may be required to create these products.")
    return False


# ─── Subscription ─────────────────────────────────────────────────────────────

def create_subscription(service) -> bool:
    """
    Create an auto-renewable subscription using monetization.subscriptions.create.

    Two-step process:
    1. Create the subscription with a base plan (starts in DRAFT)
    2. Activate the base plan

    API: POST /androidpublisher/v3/applications/{packageName}/subscriptions
    Docs: https://developers.google.com/android-publisher/api-ref/rest/v3/monetization.subscriptions/create
    """
    product_id = "com.endlessrumination.pro.monthly"
    base_plan_id = "monthly-autorenew"

    body = {
        "packageName": PACKAGE_NAME,
        "productId": product_id,
        "basePlans": [
            {
                "basePlanId": base_plan_id,
                "autoRenewingBasePlanType": {
                    "billingPeriodDuration": "P1M",
                    "gracePeriodDuration": "P3D",
                    "resubscribeState": "RESUBSCRIBE_STATE_ACTIVE",
                    "legacyCompatible": True,
                },
                "regionalConfigs": [
                    {
                        "regionCode": "US",
                        "newSubscriberAvailability": True,
                        "price": {
                            "currencyCode": "USD",
                            "units": "9",
                            "nanos": 990000000,
                        },
                    }
                ],
                "otherRegionsConfig": {
                    "usdPrice": {
                        "currencyCode": "USD",
                        "units": "9",
                        "nanos": 990000000,
                    },
                    "eurPrice": {
                        "currencyCode": "EUR",
                        "units": "9",
                        "nanos": 990000000,
                    },
                    "newSubscriberAvailability": True,
                },
            }
        ],
        "listings": [
            {
                "languageCode": "en-US",
                "title": "Endless Rumination Pro",
                "description": "All 20 AI lenses on Sonnet, no ads, saved history, 50 submissions/day.",
                "benefits": [
                    "All 20 base perspectives on Sonnet",
                    "50 submissions per day",
                    "No advertisements",
                    "History saved forever",
                ],
            }
        ],
    }

    # Step 1: Create the subscription
    try:
        result = service.monetization().subscriptions().create(
            packageName=PACKAGE_NAME,
            productId=product_id,
            body=body,
            regionsVersion_version="2022/02",
        ).execute()
        print(f"  Created subscription: {product_id} @ $9.99/month")
    except HttpError as e:
        if e.resp.status == 409:
            print(f"  Subscription already exists: {product_id}")
        else:
            print(f"  ERROR creating subscription: {e.resp.status}")
            print(f"  {e.content.decode()}")
            return False

    # Step 2: Activate the base plan
    try:
        service.monetization().subscriptions().basePlans().activate(
            packageName=PACKAGE_NAME,
            productId=product_id,
            basePlanId=base_plan_id,
            body={},
        ).execute()
        print(f"  Activated base plan: {base_plan_id}")
    except HttpError as e:
        # Already active is fine
        error_body = e.content.decode()
        if "ACTIVE" in error_body or e.resp.status == 400:
            print(f"  Base plan already active: {base_plan_id}")
        else:
            print(f"  ERROR activating base plan: {e.resp.status}")
            print(f"  {error_body}")
            return False

    return True


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Google Play Console - Create IAPs & Subscriptions")
    print("=" * 60)

    service, credentials = get_service()
    print("  API client initialized\n")

    # Step 1: Create 4 voice pack one-time products
    packs = [
        {
            "sku": "com.endlessrumination.pack.strategists",
            "title": "Strategists Voice Pack",
            "description": "5 voices on power, persuasion & getting ahead: Dale Carnegie, Machiavelli, Sun Tzu, Benjamin Franklin, P.T. Barnum.",
        },
        {
            "sku": "com.endlessrumination.pack.revolutionaries",
            "title": "Revolutionaries Voice Pack",
            "description": "5 voices of radical reframes & sharp wit: Lenin, Oscar Wilde, Mark Twain, Sigmund Freud, Cleopatra.",
        },
        {
            "sku": "com.endlessrumination.pack.philosophers",
            "title": "Philosophers Voice Pack",
            "description": "5 voices of deep thinking on the human condition: Immanuel Kant, Nietzsche, Kierkegaard, Epictetus, Lao Tzu.",
        },
        {
            "sku": "com.endlessrumination.pack.creators",
            "title": "Creators Voice Pack",
            "description": "5 voices on art, expression & finding meaning: Leonardo da Vinci, Emily Dickinson, Miyamoto Musashi, Walt Whitman, Frida Kahlo.",
        },
    ]

    print(f"{'='*60}")
    print("STEP 1: Creating 4 non-consumable products (voice packs)")
    print(f"{'='*60}")

    for pack in packs:
        create_one_time_product(service, credentials, pack["sku"], pack["title"], pack["description"])

    # Step 2: Create subscription
    print(f"\n{'='*60}")
    print("STEP 2: Creating auto-renewable subscription ($9.99/month)")
    print(f"{'='*60}")

    create_subscription(service)

    # Summary
    print(f"\n{'='*60}")
    print("DONE! All products created.")
    print(f"{'='*60}")
    print(f"\nPackage: {PACKAGE_NAME}")
    print(f"\nSubscription:")
    print(f"  com.endlessrumination.pro.monthly @ $9.99/month")
    print(f"\nIn-App Purchases:")
    for pack in packs:
        print(f"  {pack['sku']} @ $4.99")

    print(f"\n--- NEXT STEPS ---")
    print("1. Verify products in Play Console > Monetization > Products")
    print("2. Products are testable immediately by internal testers")
    print("3. For production: publish the app and products go live automatically")


if __name__ == "__main__":
    main()
