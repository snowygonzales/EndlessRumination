#!/usr/bin/env python3
"""
Create the consumable "Extra Takes" IAP in App Store Connect via REST API.

Product: com.endlessrumination.extra.takes ($0.99, CONSUMABLE)

Reuses JWT + API helpers from create_asc_products.py.

Usage:
  source backend/.venv/bin/activate && python3 scripts/create_extra_takes_product.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import jwt  # PyJWT
import requests

# --- Config (same as create_asc_products.py) ---

KEY_ID = "8YM9M9P47X"
ISSUER_ID = "e5829743-777b-4a9f-a968-30a8714fb272"
KEY_PATH = Path.home() / ".appstoreconnect" / "private_keys" / "AuthKey_8YM9M9P47X.p8"
BUNDLE_ID = "com.endlessrumination.EndlessRumination"
BASE_URL = "https://api.appstoreconnect.apple.com"

PRODUCT_ID = "com.endlessrumination.extra.takes"
PRODUCT_NAME = "3 Extra Perspectives"
PRODUCT_DISPLAY_NAME = "3 Extra Perspectives"
PRODUCT_DESCRIPTION = "Unlock 3 additional AI-generated perspectives on your current problem. Each purchase is one-time use for the current submission."
PRODUCT_PRICE = "0.99"


def generate_token() -> str:
    private_key = KEY_PATH.read_text()
    now = int(time.time())
    payload = {"iss": ISSUER_ID, "iat": now, "exp": now + 20 * 60, "aud": "appstoreconnect-v1"}
    headers = {"alg": "ES256", "kid": KEY_ID, "typ": "JWT"}
    return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)


def api_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def api_get(token: str, path: str, params: dict = None) -> dict:
    url = f"{BASE_URL}{path}" if path.startswith("/") else path
    r = requests.get(url, headers=api_headers(token), params=params)
    if r.status_code >= 400:
        print(f"GET {path} -> {r.status_code}")
        print(json.dumps(r.json(), indent=2))
        sys.exit(1)
    return r.json()


def api_post(token: str, path: str, body: dict, allow_conflict: bool = False) -> dict | None:
    url = f"{BASE_URL}{path}"
    r = requests.post(url, headers=api_headers(token), json=body)
    if r.status_code == 409 and allow_conflict:
        print(f"    (already exists, skipping)")
        return None
    if r.status_code >= 400:
        print(f"POST {path} -> {r.status_code}")
        print(json.dumps(r.json(), indent=2))
        print(f"\nRequest body was:")
        print(json.dumps(body, indent=2))
        sys.exit(1)
    return r.json()


def main():
    print("=" * 60)
    print("App Store Connect - Create Extra Takes Consumable IAP")
    print("=" * 60)

    if not KEY_PATH.exists():
        print(f"ERROR: Private key not found at {KEY_PATH}")
        sys.exit(1)

    print("\nGenerating JWT token...")
    token = generate_token()
    print("  Token generated")

    # Look up app
    print(f"\nLooking up app: {BUNDLE_ID}")
    data = api_get(token, "/v1/apps", {"filter[bundleId]": BUNDLE_ID})
    apps = data.get("data", [])
    if not apps:
        print(f"ERROR: No app found with bundle ID '{BUNDLE_ID}'")
        sys.exit(1)
    app_id = apps[0]["id"]
    print(f"  Found app ID: {app_id}")

    # Create CONSUMABLE IAP
    print(f"\nCreating consumable IAP: {PRODUCT_ID}")
    body = {
        "data": {
            "type": "inAppPurchases",
            "attributes": {
                "name": PRODUCT_NAME,
                "productId": PRODUCT_ID,
                "inAppPurchaseType": "CONSUMABLE",
                "reviewNote": "Consumable purchase that unlocks 3 additional AI-generated perspective voices for the user's current problem submission. One-time use, does not persist across submissions.",
                "familySharable": False,
            },
            "relationships": {
                "app": {
                    "data": {"type": "apps", "id": app_id}
                }
            },
        }
    }

    result = api_post(token, "/v2/inAppPurchases", body, allow_conflict=True)
    if result:
        iap_id = result["data"]["id"]
        print(f"  Created IAP: {PRODUCT_ID} (ID: {iap_id})")
    else:
        # Already exists -- look it up
        data = api_get(token, f"/v1/apps/{app_id}/inAppPurchasesV2", {"limit": 50})
        iap_id = None
        for iap in data.get("data", []):
            if iap["attributes"]["productId"] == PRODUCT_ID:
                iap_id = iap["id"]
                print(f"  Found existing IAP: {PRODUCT_ID} (ID: {iap_id})")
                break
        if not iap_id:
            print(f"  ERROR: Could not find existing IAP {PRODUCT_ID}")
            sys.exit(1)

    # Create localization
    print(f"\n  Creating en-US localization...")
    loc_body = {
        "data": {
            "type": "inAppPurchaseLocalizations",
            "attributes": {
                "name": PRODUCT_DISPLAY_NAME,
                "locale": "en-US",
                "description": PRODUCT_DESCRIPTION,
            },
            "relationships": {
                "inAppPurchaseV2": {
                    "data": {"type": "inAppPurchases", "id": iap_id}
                }
            },
        }
    }
    result = api_post(token, "/v1/inAppPurchaseLocalizations", loc_body, allow_conflict=True)
    if result:
        print(f"    Localization created (ID: {result['data']['id']})")

    # Set price to $0.99
    print(f"\n  Looking up ${PRODUCT_PRICE} price point for USA...")
    all_points = []
    url = f"/v2/inAppPurchases/{iap_id}/pricePoints"
    params = {"filter[territory]": "USA", "limit": 200}

    while url:
        data = api_get(token, url, params)
        all_points.extend(data.get("data", []))
        next_url = data.get("links", {}).get("next")
        if next_url:
            url = next_url
            params = None
        else:
            url = None

    price_point_id = None
    for point in all_points:
        if point["attributes"]["customerPrice"] == PRODUCT_PRICE:
            price_point_id = point["id"]
            proceeds = point["attributes"]["proceeds"]
            print(f"    Found: ${PRODUCT_PRICE} (proceeds: ${proceeds})")
            break

    if not price_point_id:
        available = sorted(set(p["attributes"]["customerPrice"] for p in all_points), key=float)
        print(f"    ERROR: ${PRODUCT_PRICE} not found. Available: {available[:20]}")
        sys.exit(1)

    # Set price schedule
    print(f"\n  Setting price schedule...")
    placeholder_id = "price-placeholder-extra"
    price_body = {
        "data": {
            "type": "inAppPurchasePriceSchedules",
            "relationships": {
                "inAppPurchase": {
                    "data": {"type": "inAppPurchases", "id": iap_id}
                },
                "baseTerritory": {
                    "data": {"type": "territories", "id": "USA"}
                },
                "manualPrices": {
                    "data": [
                        {"type": "inAppPurchasePrices", "id": placeholder_id}
                    ]
                },
            },
        },
        "included": [
            {
                "type": "inAppPurchasePrices",
                "id": placeholder_id,
                "attributes": {"startDate": None},
                "relationships": {
                    "inAppPurchaseV2": {
                        "data": {"type": "inAppPurchases", "id": iap_id}
                    },
                    "inAppPurchasePricePoint": {
                        "data": {"type": "inAppPurchasePricePoints", "id": price_point_id}
                    },
                },
            }
        ],
    }

    result = api_post(token, "/v1/inAppPurchasePriceSchedules", price_body, allow_conflict=True)
    if result:
        print(f"    Price schedule created (ID: {result['data']['id']})")

    print(f"\n{'='*60}")
    print(f"DONE! Consumable IAP created:")
    print(f"  Product ID: {PRODUCT_ID}")
    print(f"  ASC ID:     {iap_id}")
    print(f"  Type:       CONSUMABLE")
    print(f"  Price:      ${PRODUCT_PRICE}")
    print(f"{'='*60}")
    print(f"\nNote: Upload a review screenshot before submitting for review.")


if __name__ == "__main__":
    main()
