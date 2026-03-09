#!/usr/bin/env python3
"""
Create In-App Purchases and Subscriptions in App Store Connect via REST API.

Products to create:
  1. Auto-renewable subscription: com.endlessrumination.pro.monthly ($9.99/month)
  2. Non-consumable IAP: com.endlessrumination.pack.strategists ($4.99)
  3. Non-consumable IAP: com.endlessrumination.pack.revolutionaries ($4.99)
  4. Non-consumable IAP: com.endlessrumination.pack.philosophers ($4.99)
  5. Non-consumable IAP: com.endlessrumination.pack.creators ($4.99)

Prerequisites:
  pip install PyJWT cryptography requests

Usage:
  python3 scripts/create_asc_products.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import jwt  # PyJWT
import requests

# ─── Configuration ────────────────────────────────────────────────────────────

KEY_ID = "8YM9M9P47X"
ISSUER_ID = "e5829743-777b-4a9f-a968-30a8714fb272"
KEY_PATH = Path.home() / ".appstoreconnect" / "private_keys" / "AuthKey_8YM9M9P47X.p8"

BUNDLE_ID = "com.endlessrumination.EndlessRumination"
BASE_URL = "https://api.appstoreconnect.apple.com"

# ─── JWT Token Generation ────────────────────────────────────────────────────

def generate_token() -> str:
    """
    Generate a JWT for App Store Connect API authentication.

    JWT Header:
      - alg: ES256 (Elliptic Curve with P-256 and SHA-256)
      - kid: Your API Key ID
      - typ: JWT

    JWT Payload:
      - iss: Your Issuer ID (from App Store Connect > Users and Access > Integrations > Team Keys)
      - iat: Current time
      - exp: Expiration (max 20 minutes from iat)
      - aud: "appstoreconnect-v1" (literal string, always this value)

    The .p8 file contains a PEM-encoded ES256 private key.
    """
    private_key = KEY_PATH.read_text()

    now = int(time.time())
    payload = {
        "iss": ISSUER_ID,
        "iat": now,
        "exp": now + (20 * 60),  # 20 minutes max
        "aud": "appstoreconnect-v1",
    }
    headers = {
        "alg": "ES256",
        "kid": KEY_ID,
        "typ": "JWT",
    }

    token = jwt.encode(payload, private_key, algorithm="ES256", headers=headers)
    return token


def api_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


# ─── API Helpers ──────────────────────────────────────────────────────────────

def api_get(token: str, path: str, params: dict = None) -> dict:
    url = f"{BASE_URL}{path}"
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


# ─── Step 1: Look Up App ID ──────────────────────────────────────────────────

def get_app_id(token: str) -> str:
    """
    GET /v1/apps?filter[bundleId]=com.endlessrumination.EndlessRumination

    Returns the numeric App Store Connect app ID (e.g., "6745625039").
    This ID is required as a relationship in all product creation requests.
    """
    print(f"\n{'='*60}")
    print("STEP 1: Looking up App ID for bundle ID:", BUNDLE_ID)
    print(f"{'='*60}")

    data = api_get(token, "/v1/apps", {"filter[bundleId]": BUNDLE_ID})
    apps = data.get("data", [])

    if not apps:
        print(f"ERROR: No app found with bundle ID '{BUNDLE_ID}'")
        print("Make sure the app exists in App Store Connect.")
        sys.exit(1)

    app_id = apps[0]["id"]
    app_name = apps[0]["attributes"]["name"]
    print(f"  Found: {app_name} (ID: {app_id})")
    return app_id


# ─── Step 2: Create Non-Consumable IAPs ──────────────────────────────────────

def create_iap(token: str, app_id: str, product_id: str, name: str) -> str:
    """
    POST /v2/inAppPurchases

    Creates a non-consumable in-app purchase.

    Request body (InAppPurchaseV2CreateRequest):
    {
      "data": {
        "type": "inAppPurchases",
        "attributes": {
          "name": "...",              # Internal reference name (not shown to users)
          "productId": "...",         # The product identifier used in StoreKit
          "inAppPurchaseType": "NON_CONSUMABLE",  # Enum: CONSUMABLE, NON_CONSUMABLE, NON_RENEWING_SUBSCRIPTION
          "reviewNote": "...",        # Optional note for App Review
          "familySharable": false     # Optional, whether Family Sharing is enabled
        },
        "relationships": {
          "app": {
            "data": {
              "type": "apps",
              "id": "<app_id>"
            }
          }
        }
      }
    }

    Returns the created IAP's ID.
    """
    body = {
        "data": {
            "type": "inAppPurchases",
            "attributes": {
                "name": name,
                "productId": product_id,
                "inAppPurchaseType": "NON_CONSUMABLE",
                "reviewNote": "This voice pack unlocks 5 additional AI-generated perspective voices in the Endless Rumination app.",
                "familySharable": False,
            },
            "relationships": {
                "app": {
                    "data": {
                        "type": "apps",
                        "id": app_id,
                    }
                }
            },
        }
    }

    result = api_post(token, "/v2/inAppPurchases", body, allow_conflict=True)
    if result:
        iap_id = result["data"]["id"]
        print(f"  Created IAP: {product_id} (ID: {iap_id})")
        return iap_id

    # Already exists — look it up via app's inAppPurchases relationship
    data = api_get(token, f"/v1/apps/{app_id}/inAppPurchasesV2", {
        "limit": 50,
    })
    for iap in data.get("data", []):
        if iap["attributes"]["productId"] == product_id:
            iap_id = iap["id"]
            print(f"  Found existing IAP: {product_id} (ID: {iap_id})")
            return iap_id

    print(f"  ERROR: Could not find existing IAP {product_id}")
    sys.exit(1)


def create_iap_localization(token: str, iap_id: str, name: str, description: str) -> str:
    """
    POST /v1/inAppPurchaseLocalizations

    Creates a localization for an in-app purchase. At least one localization
    (en-US) is required for the IAP to be submittable for review.

    Request body (InAppPurchaseLocalizationCreateRequest):
    {
      "data": {
        "type": "inAppPurchaseLocalizations",
        "attributes": {
          "name": "...",           # Display name shown to users
          "locale": "en-US",      # BCP 47 locale code
          "description": "..."    # Description shown on the App Store
        },
        "relationships": {
          "inAppPurchaseV2": {
            "data": {
              "type": "inAppPurchases",
              "id": "<iap_id>"
            }
          }
        }
      }
    }
    """
    body = {
        "data": {
            "type": "inAppPurchaseLocalizations",
            "attributes": {
                "name": name,
                "locale": "en-US",
                "description": description,
            },
            "relationships": {
                "inAppPurchaseV2": {
                    "data": {
                        "type": "inAppPurchases",
                        "id": iap_id,
                    }
                }
            },
        }
    }

    result = api_post(token, "/v1/inAppPurchaseLocalizations", body, allow_conflict=True)
    if result:
        loc_id = result["data"]["id"]
        print(f"    Localization created (ID: {loc_id})")
        return loc_id
    return "existing"


def find_iap_price_point(token: str, iap_id: str, target_price: str, territory: str = "USA") -> str:
    """
    GET /v2/inAppPurchases/{id}/pricePoints?filter[territory]=USA

    Retrieves all available price points for an IAP filtered by territory.
    Each price point has a customerPrice (e.g., "4.99") and an ID.
    We search for the one matching our target price.

    Response includes objects like:
    {
      "type": "inAppPurchasePricePoints",
      "id": "eyJ...",
      "attributes": {
        "customerPrice": "4.99",
        "proceeds": "3.49"
      }
    }

    The price point ID is an opaque base64-encoded string, not a simple number.
    """
    print(f"    Looking up price point for ${target_price} in {territory}...")

    all_points = []
    url = f"/v2/inAppPurchases/{iap_id}/pricePoints"
    params = {"filter[territory]": territory, "limit": 200}

    while url:
        data = api_get(token, url, params)
        all_points.extend(data.get("data", []))
        # Handle pagination
        next_url = data.get("links", {}).get("next")
        if next_url:
            url = next_url.replace(BASE_URL, "")
            params = None  # params are already in the next URL
        else:
            url = None

    for point in all_points:
        price = point["attributes"]["customerPrice"]
        if price == target_price:
            pp_id = point["id"]
            proceeds = point["attributes"]["proceeds"]
            print(f"    Found price point: ${price} (proceeds: ${proceeds}, ID: {pp_id[:30]}...)")
            return pp_id

    # If exact match not found, show available prices for debugging
    available = sorted(set(p["attributes"]["customerPrice"] for p in all_points), key=float)
    print(f"    ERROR: Price ${target_price} not found. Available prices: {available[:20]}...")
    sys.exit(1)


def set_iap_price(token: str, iap_id: str, price_point_id: str) -> str:
    """
    POST /v1/inAppPurchasePriceSchedules

    Sets the price schedule for a non-consumable IAP.
    This uses an "included" array pattern where inline objects define the prices.

    Request body (InAppPurchasePriceScheduleCreateRequest):
    {
      "data": {
        "type": "inAppPurchasePriceSchedules",
        "relationships": {
          "inAppPurchase": {
            "data": { "type": "inAppPurchases", "id": "<iap_id>" }
          },
          "baseTerritory": {
            "data": { "type": "territories", "id": "USA" }
          },
          "manualPrices": {
            "data": [
              { "type": "inAppPurchasePrices", "id": "${price-ref}" }
            ]
          }
        }
      },
      "included": [
        {
          "type": "inAppPurchasePrices",
          "id": "${price-ref}",           # Temporary placeholder ID (any string)
          "attributes": {
            "startDate": null              # null = effective immediately
          },
          "relationships": {
            "inAppPurchaseV2": {
              "data": { "type": "inAppPurchases", "id": "<iap_id>" }
            },
            "inAppPurchasePricePoint": {
              "data": { "type": "inAppPurchasePricePoints", "id": "<price_point_id>" }
            }
          }
        }
      ]
    }

    Notes:
    - The "id" in the manualPrices data array and the "id" in the included array
      must match, but can be any arbitrary string (Apple replaces it).
    - baseTerritory "USA" means the US price is the reference price;
      Apple auto-equalizes prices for other territories.
    - startDate: null means the price takes effect immediately.
    """
    placeholder_id = "price-placeholder-1"

    body = {
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
                "attributes": {
                    "startDate": None,  # Effective immediately
                },
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

    result = api_post(token, "/v1/inAppPurchasePriceSchedules", body, allow_conflict=True)
    if result:
        schedule_id = result["data"]["id"]
        print(f"    Price schedule created (ID: {schedule_id})")
        return schedule_id
    return "existing"


# ─── Step 3: Create Subscription Group ────────────────────────────────────────

def create_subscription_group(token: str, app_id: str) -> str:
    """
    POST /v1/subscriptionGroups

    Creates a subscription group. All auto-renewable subscriptions must
    belong to a group. A user can only be subscribed to one product within
    a group at a time (used for upgrade/downgrade/crossgrade).

    Request body (SubscriptionGroupCreateRequest):
    {
      "data": {
        "type": "subscriptionGroups",
        "attributes": {
          "referenceName": "..."    # Internal name (not shown to users)
        },
        "relationships": {
          "app": {
            "data": { "type": "apps", "id": "<app_id>" }
          }
        }
      }
    }
    """
    print(f"\n{'='*60}")
    print("STEP 3: Creating subscription group")
    print(f"{'='*60}")

    body = {
        "data": {
            "type": "subscriptionGroups",
            "attributes": {
                "referenceName": "Endless Rumination Pro",
            },
            "relationships": {
                "app": {
                    "data": {"type": "apps", "id": app_id}
                }
            },
        }
    }

    result = api_post(token, "/v1/subscriptionGroups", body, allow_conflict=True)
    if result:
        group_id = result["data"]["id"]
        print(f"  Created subscription group: Endless Rumination Pro (ID: {group_id})")
        return group_id

    # Already exists — look it up
    data = api_get(token, f"/v1/apps/{app_id}/subscriptionGroups", {"limit": 50})
    for group in data.get("data", []):
        if group["attributes"]["referenceName"] == "Endless Rumination Pro":
            group_id = group["id"]
            print(f"  Found existing subscription group: Endless Rumination Pro (ID: {group_id})")
            return group_id

    print("  ERROR: Could not find existing subscription group")
    sys.exit(1)


def create_subscription_group_localization(token: str, group_id: str) -> str:
    """
    POST /v1/subscriptionGroupLocalizations

    Creates a localization for the subscription group.
    The group name is displayed in the App Store subscription management UI.

    Request body (SubscriptionGroupLocalizationCreateRequest):
    {
      "data": {
        "type": "subscriptionGroupLocalizations",
        "attributes": {
          "name": "...",             # Displayed group name
          "locale": "en-US",        # BCP 47 locale
          "customAppName": null     # Optional custom app name for this group
        },
        "relationships": {
          "subscriptionGroup": {
            "data": { "type": "subscriptionGroups", "id": "<group_id>" }
          }
        }
      }
    }
    """
    body = {
        "data": {
            "type": "subscriptionGroupLocalizations",
            "attributes": {
                "name": "Endless Rumination Pro",
                "locale": "en-US",
            },
            "relationships": {
                "subscriptionGroup": {
                    "data": {"type": "subscriptionGroups", "id": group_id}
                }
            },
        }
    }

    result = api_post(token, "/v1/subscriptionGroupLocalizations", body, allow_conflict=True)
    if result:
        loc_id = result["data"]["id"]
        print(f"  Group localization created (ID: {loc_id})")
        return loc_id
    return "existing"


# ─── Step 4: Create Subscription ─────────────────────────────────────────────

def create_subscription(token: str, group_id: str, app_id: str) -> str:
    """
    POST /v1/subscriptions

    Creates an auto-renewable subscription within a group.

    Request body (SubscriptionCreateRequest):
    {
      "data": {
        "type": "subscriptions",
        "attributes": {
          "name": "...",                # Internal reference name
          "productId": "...",           # StoreKit product identifier
          "subscriptionPeriod": "...",  # Enum: ONE_WEEK, ONE_MONTH, TWO_MONTHS,
                                        #        THREE_MONTHS, SIX_MONTHS, ONE_YEAR
          "familySharable": false,      # Optional
          "reviewNote": "...",          # Optional note for App Review
          "groupLevel": 1              # Optional: ranking within the group (1 = highest)
        },
        "relationships": {
          "group": {
            "data": { "type": "subscriptionGroups", "id": "<group_id>" }
          }
        }
      }
    }
    """
    print(f"\n{'='*60}")
    print("STEP 4: Creating auto-renewable subscription")
    print(f"{'='*60}")

    body = {
        "data": {
            "type": "subscriptions",
            "attributes": {
                "name": "Pro Monthly",
                "productId": "com.endlessrumination.pro.monthly",
                "subscriptionPeriod": "ONE_MONTH",
                "familySharable": False,
                "reviewNote": "Pro subscription unlocks all 20 AI perspective lenses (upgraded to Sonnet quality), removes ads, saves history, and allows 50 submissions per day.",
                "groupLevel": 1,
            },
            "relationships": {
                "group": {
                    "data": {"type": "subscriptionGroups", "id": group_id}
                }
            },
        }
    }

    result = api_post(token, "/v1/subscriptions", body, allow_conflict=True)
    if result:
        sub_id = result["data"]["id"]
        print(f"  Created subscription: com.endlessrumination.pro.monthly (ID: {sub_id})")
        return sub_id

    # Already exists — look it up via app's subscription groups
    data = api_get(token, f"/v1/apps/{app_id}/subscriptionGroups", {"limit": 50})
    for group in data.get("data", []):
        subs_data = api_get(token, f"/v1/subscriptionGroups/{group['id']}/subscriptions", {"limit": 50})
        for sub in subs_data.get("data", []):
            if sub["attributes"]["productId"] == "com.endlessrumination.pro.monthly":
                sub_id = sub["id"]
                print(f"  Found existing subscription: com.endlessrumination.pro.monthly (ID: {sub_id})")
                return sub_id

    print("  ERROR: Could not find existing subscription")
    sys.exit(1)


def create_subscription_localization(token: str, sub_id: str) -> str:
    """
    POST /v1/subscriptionLocalizations

    Creates a localization for the subscription product.

    Request body (SubscriptionLocalizationCreateRequest):
    {
      "data": {
        "type": "subscriptionLocalizations",
        "attributes": {
          "name": "...",           # Display name shown to users
          "locale": "en-US",
          "description": "..."    # Description shown on App Store
        },
        "relationships": {
          "subscription": {
            "data": { "type": "subscriptions", "id": "<sub_id>" }
          }
        }
      }
    }
    """
    body = {
        "data": {
            "type": "subscriptionLocalizations",
            "attributes": {
                "name": "Pro Monthly",
                "locale": "en-US",
                "description": "All 20 AI lenses on Sonnet, no ads, saved history, 50 submissions/day.",
            },
            "relationships": {
                "subscription": {
                    "data": {"type": "subscriptions", "id": sub_id}
                }
            },
        }
    }

    result = api_post(token, "/v1/subscriptionLocalizations", body, allow_conflict=True)
    if result:
        loc_id = result["data"]["id"]
        print(f"  Subscription localization created (ID: {loc_id})")
        return loc_id
    return "existing"


def find_subscription_price_point(token: str, sub_id: str, target_price: str, territory: str = "USA") -> str:
    """
    GET /v1/subscriptions/{id}/pricePoints?filter[territory]=USA

    Retrieves available price points for a subscription.
    Same pattern as IAP price points but uses subscriptionPricePoints type.

    Response includes objects like:
    {
      "type": "subscriptionPricePoints",
      "id": "eyJ...",
      "attributes": {
        "customerPrice": "9.99",
        "proceeds": "6.99"
      }
    }
    """
    print(f"  Looking up subscription price point for ${target_price} in {territory}...")

    all_points = []
    url = f"/v1/subscriptions/{sub_id}/pricePoints"
    params = {"filter[territory]": territory, "limit": 200}

    while url:
        data = api_get(token, url, params)
        all_points.extend(data.get("data", []))
        next_url = data.get("links", {}).get("next")
        if next_url:
            url = next_url.replace(BASE_URL, "")
            params = None
        else:
            url = None

    for point in all_points:
        price = point["attributes"]["customerPrice"]
        if price == target_price:
            pp_id = point["id"]
            proceeds = point["attributes"]["proceeds"]
            print(f"  Found price point: ${price} (proceeds: ${proceeds}, ID: {pp_id[:30]}...)")
            return pp_id

    available = sorted(set(p["attributes"]["customerPrice"] for p in all_points), key=float)
    print(f"  ERROR: Price ${target_price} not found. Available prices: {available[:20]}...")
    sys.exit(1)


def set_subscription_price(token: str, sub_id: str, price_point_id: str) -> str:
    """
    POST /v1/subscriptionPrices

    Sets the price for a subscription in a specific territory.

    Request body (SubscriptionPriceCreateRequest):
    {
      "data": {
        "type": "subscriptionPrices",
        "attributes": {
          "startDate": null,                # null = effective immediately
          "preserveCurrentPrice": false     # Whether existing subscribers keep old price
        },
        "relationships": {
          "subscription": {
            "data": { "type": "subscriptions", "id": "<sub_id>" }
          },
          "subscriptionPricePoint": {
            "data": { "type": "subscriptionPricePoints", "id": "<price_point_id>" }
          }
        }
      }
    }

    Note: Unlike IAP pricing (which uses inAppPurchasePriceSchedules with
    baseTerritory + manualPrices + included array), subscription pricing
    uses a simpler direct POST to /v1/subscriptionPrices for each territory.
    Setting the USA price point will auto-equalize other territories.
    """
    body = {
        "data": {
            "type": "subscriptionPrices",
            "attributes": {
                "startDate": None,
                "preserveCurrentPrice": False,
            },
            "relationships": {
                "subscription": {
                    "data": {"type": "subscriptions", "id": sub_id}
                },
                "subscriptionPricePoint": {
                    "data": {"type": "subscriptionPricePoints", "id": price_point_id}
                },
            },
        }
    }

    result = api_post(token, "/v1/subscriptionPrices", body, allow_conflict=True)
    if result:
        price_id = result["data"]["id"]
        print(f"  Subscription price set (ID: {price_id})")
        return price_id
    print(f"  Subscription price already set")
    return "existing"


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("App Store Connect - Create IAPs & Subscriptions")
    print("=" * 60)

    # Verify key exists
    if not KEY_PATH.exists():
        print(f"ERROR: Private key not found at {KEY_PATH}")
        sys.exit(1)

    # Generate JWT
    print("\nGenerating JWT token...")
    token = generate_token()
    print("  Token generated (valid for 20 minutes)")

    # Step 1: Look up the app
    app_id = get_app_id(token)

    # Step 2: Create 4 non-consumable IAPs (voice packs)
    iap_products = [
        {
            "product_id": "com.endlessrumination.pack.strategists",
            "name": "Strategists Voice Pack",
            "display_name": "Strategists Pack",
            "description": "5 voices on power, persuasion & getting ahead: Dale Carnegie, Machiavelli, Sun Tzu, Benjamin Franklin, P.T. Barnum.",
        },
        {
            "product_id": "com.endlessrumination.pack.revolutionaries",
            "name": "Revolutionaries Voice Pack",
            "display_name": "Revolutionaries Pack",
            "description": "5 voices of radical reframes & sharp wit: Lenin, Oscar Wilde, Mark Twain, Sigmund Freud, Cleopatra.",
        },
        {
            "product_id": "com.endlessrumination.pack.philosophers",
            "name": "Philosophers Voice Pack",
            "display_name": "Philosophers Pack",
            "description": "5 voices of deep thinking on the human condition: Immanuel Kant, Nietzsche, Kierkegaard, Epictetus, Lao Tzu.",
        },
        {
            "product_id": "com.endlessrumination.pack.creators",
            "name": "Creators Voice Pack",
            "display_name": "Creators Pack",
            "description": "5 voices on art, expression & finding meaning: Leonardo da Vinci, Emily Dickinson, Miyamoto Musashi, Walt Whitman, Frida Kahlo.",
        },
    ]

    print(f"\n{'='*60}")
    print("STEP 2: Creating 4 non-consumable IAPs (voice packs)")
    print(f"{'='*60}")

    iap_ids = {}
    for product in iap_products:
        # 2a. Create the IAP
        iap_id = create_iap(token, app_id, product["product_id"], product["name"])
        iap_ids[product["product_id"]] = iap_id

        # 2b. Create en-US localization
        create_iap_localization(token, iap_id, product["display_name"], product["description"])

        # 2c. Find the $4.99 price point for USA
        price_point_id = find_iap_price_point(token, iap_id, "4.99", "USA")

        # 2d. Set the price
        set_iap_price(token, iap_id, price_point_id)

        print()

    # Step 3: Create subscription group
    group_id = create_subscription_group(token, app_id)
    create_subscription_group_localization(token, group_id)

    # Step 4: Create subscription
    sub_id = create_subscription(token, group_id, app_id)
    create_subscription_localization(token, sub_id)

    # Step 5: Set subscription price
    print(f"\n{'='*60}")
    print("STEP 5: Setting subscription price ($9.99/month)")
    print(f"{'='*60}")

    price_point_id = find_subscription_price_point(token, sub_id, "9.99", "USA")
    set_subscription_price(token, sub_id, price_point_id)

    # Summary
    print(f"\n{'='*60}")
    print("DONE! All products created successfully.")
    print(f"{'='*60}")
    print(f"\nApp ID: {app_id}")
    print(f"\nSubscription Group ID: {group_id}")
    print(f"Subscription ID: {sub_id}")
    print(f"  Product: com.endlessrumination.pro.monthly @ $9.99/month")
    print(f"\nIn-App Purchases:")
    for product in iap_products:
        pid = product["product_id"]
        print(f"  {pid} (ID: {iap_ids[pid]}) @ $4.99")

    print(f"\n--- NEXT STEPS ---")
    print("1. Upload review screenshots for each product (required for submission)")
    print("   - Subscriptions: POST /v1/subscriptionAppStoreReviewScreenshots")
    print("   - IAPs: POST /v1/inAppPurchaseAppStoreReviewScreenshots")
    print("2. Submit for review:")
    print("   - Subscription: POST /v1/subscriptionSubmissions")
    print("   - IAPs: POST /v1/inAppPurchaseSubmissions")
    print("3. Or submit everything together with the next app version")


if __name__ == "__main__":
    main()
