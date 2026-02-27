# CLAUDE.md — Endless Rumination

## Project Overview
Psychology app with two independent native frontends (SwiftUI iOS + Jetpack Compose Android) + Python backend (FastAPI). Users describe a problem, then doom-scroll through AI-generated perspectives from different personas. Each perspective fades forever unless user is a Pro subscriber. Base lenses (0-19) come with free/Pro tiers; purchasable Voice Packs (20-39) add 5 historical-figure voices each.

**Architecture:** Two fully native apps sharing code by convention (same API contract, models, design system, business rules) — not by shared code. The backend is platform-agnostic. KMP (Compose Multiplatform) was previously used but abandoned due to rendering quality issues on iOS; `multiplatform/` is archived as reference only.

## Key Commands
- Backend (local): `cd backend && source .venv/bin/activate && uvicorn app.main:app --reload`
- Backend (Docker): `cd backend && docker-compose up`
- Backend tests: `cd backend && pytest -v` (42 tests, all passing — SQLite + mocked Claude)
- iOS project: `cd ios && xcodegen generate && open EndlessRumination.xcodeproj`
- iOS tests: Cmd+U in Xcode (9 tests)
- iOS TestFlight: `cd ios && xcodegen generate && xcodebuild -scheme EndlessRumination -sdk iphoneos -configuration Release -archivePath /tmp/ER-iOS.xcarchive archive && xcodebuild -exportArchive -archivePath /tmp/ER-iOS.xcarchive -exportOptionsPlist /tmp/ExportOptions.plist -exportPath /tmp/ER-iOS-Export -allowProvisioningUpdates -authenticationKeyPath ~/.appstoreconnect/private_keys/AuthKey_8YM9M9P47X.p8 -authenticationKeyID 8YM9M9P47X -authenticationKeyIssuerID e5829743-777b-4a9f-a968-30a8714fb272`
- Android build: `cd android && JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew :app:assembleDebug`
- Android install: `~/Library/Android/sdk/platform-tools/adb install -r android/app/build/outputs/apk/debug/app-debug.apk`
- Android release: `cd android && JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew :app:bundleRelease`
- Android publish to Play Internal Testing: `cd android && JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew :app:publishReleaseBundle` (requires `play-service-account.json`)
- Android emulator: `~/Library/Android/sdk/emulator/emulator -avd Pixel_API_35 &`
- Deploy to Railway: `railway up --detach` (from project root)

## Architecture
- Two native frontends → FastAPI gateway → Claude Sonnet/Haiku hybrid API
- Free tier: 5 lenses (2 Sonnet "Wise" at indices 1,9 + 3 Haiku), 3 submissions/month
- Pro ($9.99/mo): All 20 base lenses on Sonnet, 50/day, no ads, history saved
- Voice Packs ($4.99 each, non-consumable IAP): 4 packs × 5 voices (indices 20-39), all Sonnet
  - Strategists (20-24), Revolutionaries (25-29), Philosophers (30-34), Creators (35-39)
  - Pack voices append after base takes in the doom scroll
- PostgreSQL for users/takes, Redis for rate limiting (optional, degrades gracefully)
- SSE streaming for real-time take delivery
- xcodegen for iOS Xcode project generation (project.yml → .xcodeproj)

## Directory Structure
```
EndlessRumination/
├── backend/                    # FastAPI backend (Python)
├── ios/                        # SwiftUI native iOS app
├── android/                    # Jetpack Compose native Android app
├── multiplatform/              # ARCHIVED — KMP reference code only
├── docs/
├── CLAUDE.md
└── KICKOFF.md
```

## Environment & Infrastructure
- **Machine**: Mac Mini M1, macOS, Xcode 16, Python 3.9
- **JDK**: OpenJDK 17 via Homebrew (`JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home`)
- **Android SDK**: `~/Library/Android/sdk` (cmdline-tools, platform-tools, emulator, API 35 ARM64)
- **iOS simulator**: iPhone 17 Pro (ID: `8C545099-AF9E-4D62-A716-E0826851F18D`)
- **Production API**: https://backend-production-5537.up.railway.app
- **Railway dashboard**: https://railway.com/project/30951286-357e-4529-a21c-bb527d62eb13
- **Privacy policy**: https://github.com/snowygonzales/EndlessRumination/blob/master/docs/privacy-policy.md
- **Support page**: https://github.com/snowygonzales/EndlessRumination/blob/master/docs/support.md
- iOS debug builds → localhost:8000, release builds → Railway URL
- Android always uses Railway production URL
- PostgreSQL 16 + Redis via Homebrew (not Docker)

### CLI Publishing (both platforms — no GUI needed)
- **iOS → TestFlight**: App Store Connect API key `8YM9M9P47X` at `~/.appstoreconnect/private_keys/AuthKey_8YM9M9P47X.p8`, Issuer `e5829743-777b-4a9f-a968-30a8714fb272`. Bundle ID: `com.endlessrumination.EndlessRumination`. ExportOptions plist at `/tmp/ExportOptions.plist` (method: app-store-connect, teamID: R6N5B4SDWH, destination: upload, signingStyle: automatic).
- **Android → Google Play Internal Testing**: Google Cloud service account (`play-service-account.json` in `android/`, gitignored) linked via Google Play Console Users & Permissions — `./gradlew :app:publishReleaseBundle` builds signed AAB + uploads to internal track
- **Google Play Console**: Account ID `6253718630117210435`, app package `com.endlessrumination`, developer identity verification pending (draft releases only until verified)
- **Google Cloud project**: `endless-rumination` — Android Publisher API enabled, service account created and linked to Play Console

## Important Files

### iOS (SwiftUI)
- `ios/project.yml` — xcodegen project definition (SPM packages, build settings, Info.plist)
- `ios/EndlessRumination/App/EndlessRuminationApp.swift` — App entry point, GAD init
- `ios/EndlessRumination/App/AppState.swift` — @Observable state management
- `ios/EndlessRumination/Services/APIClient.swift` — URLSession HTTP + SSE streaming actor
- `ios/EndlessRumination/Services/SubscriptionManager.swift` — StoreKit 2 billing, receipt verification
- `ios/EndlessRumination/Services/SafetyService.swift` — Client blocklist + server safety check
- `ios/EndlessRumination/Models/` — Take, Lens, VoicePack, User
- `ios/EndlessRumination/Views/` — All 11 screens + AdBannerView (real GADBannerView)
- `ios/EndlessRumination/Theme/` — ERColors, ERTypography, ERAnimations

### Android (Jetpack Compose)
- `android/app/build.gradle.kts` — App build config (Compose BOM, Ktor, billing, ads, signing)
- `android/app/src/main/kotlin/.../MainActivity.kt` — Activity entry point, MobileAds + HapticService init
- `android/app/src/main/kotlin/.../App.kt` — Root composable, AnimatedContent navigation, billing lifecycle
- `android/app/src/main/kotlin/.../AppState.kt` — ViewModel state management (mutableStateOf, BillingCallback)
- `android/app/src/main/kotlin/.../ApiClient.kt` — Ktor HTTP + SSE streaming
- `android/app/src/main/kotlin/.../Platform.kt` — BASE_URL constant
- `android/app/src/main/kotlin/.../service/BillingService.kt` — Google Play Billing v7
- `android/app/src/main/kotlin/.../service/BillingModels.kt` — Billing types, sealed classes, product IDs
- `android/app/src/main/kotlin/.../service/HapticService.kt` — Vibration feedback
- `android/app/src/main/kotlin/.../service/SafetyService.kt` — Client blocklist + server safety check
- `android/app/src/main/kotlin/.../service/ActivityProvider.kt` — Activity context for billing
- `android/app/src/main/kotlin/.../model/` — Take, Lens, VoicePack, User
- `android/app/src/main/kotlin/.../ui/` — All 11 screens + PlatformAdBanner (AndroidView wrapping AdView)
- `android/app/src/main/kotlin/.../theme/` — ERColors, ERTypography

### Backend
- `KICKOFF.md` — Complete project spec, read this FIRST
- `reference/mockup.jsx` — React prototype with exact design specs (DO NOT build React, extract design only)
- `reference/sample_takes.json` — Quality bar for AI-generated takes
- `backend/app/lenses/definitions.py` — Base 20 lens system prompts (indices 0-19)
- `backend/app/lenses/voice_packs.py` — Voice pack definitions (indices 20-39, 4 packs × 5 voices)
- `backend/app/services/receipt_validator.py` — Abstract receipt validation base
- `backend/app/services/apple_validator.py` — App Store Server API v2 validation
- `backend/app/services/google_validator.py` — Google Play Developer API validation
- `railway.toml` — Railway deployment config

### Scripts
- `scripts/create_asc_products.py` — Creates/updates all IAP products in App Store Connect via REST API (JWT auth, idempotent)

### Archived
- `multiplatform/` — KMP Compose Multiplatform code (archived, reference only)

## Conventions
- Swift: SwiftUI only, iOS 17+, @Observable (not Combine), no UIKit unless necessary, no third-party UI deps
- Kotlin: Jetpack Compose, ViewModel for state, Ktor for networking, Material Icons (not SF Symbols)
- Python: FastAPI, async everywhere, type hints, Pydantic models, `from __future__ import annotations` (Python 3.9 compat)
- All lens system prompts end with the standard format instruction (see KICKOFF.md)
- Color values defined in KICKOFF.md are authoritative — match exactly
- API cost: ~$0.013/free submission (2 Sonnet + 3 Haiku), ~$0.12/Pro submission (20 Sonnet), ~$0.025 per pack (5 Sonnet)
- "Wise" badge on Sonnet takes (including all pack voices), "Quick take · Powered by Haiku" on Haiku takes
- Triple-tap Shop button in DEBUG builds to toggle Pro status (simulator cheat)
- Voice pack indices 20-39 extend the base lens system; `Lens.displayInfo(index)` provides unified lookup (Kotlin), `Lens.displayInfo(at:)` (Swift)
- State-based nav: `AppScreen` enum + `when` (Kotlin) / `switch` (Swift)

## Android Distribution (Google Play Internal Testing)
Google Play Internal Testing is the Android equivalent of TestFlight. Uses `gradle-play-publisher` plugin for CLI uploads. **Full CLI pipeline verified and working.**

**Setup (all complete):**
1. Release keystore at `android/release.keystore` (gitignored), credentials in `android/keystore.properties` (gitignored)
2. `gradle-play-publisher` plugin (`com.github.triplet.play:3.11.0`) configured in `app/build.gradle.kts`
3. Play Console: app `com.endlessrumination` created, Internal Testing track set up with initial AAB upload
4. Google Cloud: `endless-rumination` project, Android Publisher API enabled, service account created
5. Service account linked to Play Console via Users & Permissions (not Setup → API access, which no longer exists)
6. Service account JSON key at `android/play-service-account.json` (gitignored)

**CLI publish flow:**
- `cd android && JAVA_HOME=... ./gradlew :app:publishReleaseBundle` — builds signed AAB + uploads to internal testing
- Currently creates draft releases (`ReleaseStatus.DRAFT`) due to pending developer identity verification
- Once verified: change to `ReleaseStatus.COMPLETED` in `app/build.gradle.kts` for auto-rollout to testers
- Testers get notified in Play Store → install/update via normal Play Store flow
- No "Install from unknown sources" needed, auto-updates work
- Remember to bump `versionCode` in `app/build.gradle.kts` before each publish (currently at 6)

## Monetization (IAP + Ads + Backend Validation)

### IAP Product Setup (App Store Connect)
All 5 iOS IAP products are created and priced in App Store Connect via `scripts/create_asc_products.py`:

| Product ID | Type | Price | ASC ID |
|-----------|------|-------|--------|
| `com.endlessrumination.pro.monthly` | Auto-renewable subscription | $9.99/mo | 6759655515 |
| `com.endlessrumination.pack.strategists` | Non-consumable | $4.99 | 6759794696 |
| `com.endlessrumination.pack.revolutionaries` | Non-consumable | $4.99 | 6759794840 |
| `com.endlessrumination.pack.philosophers` | Non-consumable | $4.99 | 6759794841 |
| `com.endlessrumination.pack.creators` | Non-consumable | $4.99 | 6759794982 |

- Subscription group: "Endless Rumination Pro" (ID: 21952994)
- All products have en-US localizations and USD pricing set
- Script is idempotent (handles 409 conflicts, looks up existing products)
- **To re-run**: `source backend/.venv/bin/activate && python3 scripts/create_asc_products.py` (requires PyJWT, cryptography, requests)
- **Remaining steps**: Upload review screenshots for each product, then submit with next app version
- **Google Play**: Products need to be created via Play Console once developer identity verification clears (API product creation requires published app)

### iOS Billing (StoreKit 2)
- `SubscriptionManager` — @Observable, uses StoreKit 2 async APIs directly
- `Transaction.currentEntitlements` on launch (no Apple ID prompt)
- `verifyReceiptOnServer()` called after each purchase (background, non-blocking)
- Restore purchases button in ShopView

### Android Billing (Google Play Billing v7)
- `BillingService` — standalone class wrapping `BillingClient`
- `AppState : ViewModel(), BillingCallback` — receives purchase state changes
- `App.kt` lifecycle: `LaunchedEffect` → `initialize()` + `loadProducts()` + `checkEntitlements()`; `DisposableEffect` → `dispose()`
- Product IDs: `com.endlessrumination.pro.monthly` (subscription), `com.endlessrumination.pack.{strategists,revolutionaries,philosophers,creators}` (one-time)

### AdMob (real IDs on both platforms)
- **iOS**: `BannerAdRepresentable` (UIViewRepresentable wrapping GADBannerView), ad unit `ca-app-pub-5300605522420042/1359255336`, debug uses test ID `ca-app-pub-3940256099942544/2435281174`
- **Android**: `PlatformAdBanner` (AndroidView wrapping AdView), ad unit `ca-app-pub-5300605522420042/6942754502`
- **iOS SDK**: Google Mobile Ads 11.13.0 via SPM
- **Android SDK**: play-services-ads 23.6.0
- **AndroidManifest.xml**: AdMob app ID `ca-app-pub-5300605522420042~5657592998`
- **iOS Info.plist**: `GADApplicationIdentifier` = `ca-app-pub-5300605522420042~6341428784`, plus SKAdNetwork IDs
- Banner shown on TakesScreen when `!isPro`, 50dp height

### Backend Receipt Validation
- **`POST /api/v1/subscription/verify-receipt`** — routes to Apple or Google validator by `platform` field
- **Apple**: App Store Server API v2 with JWT auth (.p8 key) → GET signed transaction → decode JWS → extract productId/expiry
- **Google**: Google Play Developer API with service account → `subscriptionsv2.get` / `products.get`
- Config: `apple_key_id`, `apple_issuer_id`, `apple_private_key_path`, `google_play_service_account_json` in Settings
- Updates user `subscription_tier` (pro) or `owned_pack_ids` (comma-separated) in DB
- Client calls verify receipt after each successful purchase (background, non-blocking)
- 7 backend tests in `test_subscription.py` (mocked validators)

## Tech Stacks

### iOS
- SwiftUI, iOS 17+, @Observable
- URLSession for HTTP + SSE (async/await)
- StoreKit 2 for IAP
- Google Mobile Ads 11.13.0 via SPM
- xcodegen for project generation

### Android
- Jetpack Compose (BOM 2024.12.01), Material3
- Ktor 3.1.1 (OkHttp engine) for HTTP + SSE
- Kotlinx.serialization 1.8.0, Kotlinx.coroutines 1.10.1
- Google Play Billing v7 (billing-ktx 7.1.1)
- play-services-ads 23.6.0
- Kotlin 2.1.20, AGP 8.7.3, Gradle 8.11.1
- min SDK 26, target SDK 35
- Requires JAVA_HOME pointing to OpenJDK 17

## What NOT to Do
- Don't build a React/web app
- Don't use UIKit storyboards
- Don't use KMP/Compose Multiplatform (archived, use native only)
- Don't hardcode API keys — use environment variables
- Don't persist free-tier takes to database
- Don't skip the safety check before generating takes
- Don't commit .xcodeproj — it's generated by xcodegen and gitignored
- Don't commit .venv or .env
