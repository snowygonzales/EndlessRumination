# CLAUDE.md — Endless Rumination

## Project Overview
Psychology app (KMP multiplatform) + Python backend (FastAPI). Users describe a problem, then doom-scroll through AI-generated perspectives from different personas. Each perspective fades forever unless user is a Pro subscriber. Base lenses (0-19) come with free/Pro tiers; purchasable Voice Packs (20-39) add 5 historical-figure voices each.

**Multiplatform (primary):** KMP + Compose Multiplatform in `multiplatform/` targets both iOS and Android from shared Kotlin code. All 11 screens, real billing (Google Play Billing v7 + StoreKit 2 via Swift bridge), AdMob ads (real on both platforms), and backend receipt validation are implemented. The original SwiftUI app in `ios/` is archived as reference code — all active development is in `multiplatform/`.

## Key Commands
- Backend (local): `cd backend && source .venv/bin/activate && uvicorn app.main:app --reload`
- Backend (Docker): `cd backend && docker-compose up`
- Backend tests: `cd backend && pytest -v` (42 tests, all passing — SQLite + mocked Claude)
- iOS project: `cd ios && xcodegen generate && open EndlessRumination.xcodeproj`
- iOS tests: Cmd+U in Xcode (9 tests)
- KMP Android build: `cd multiplatform && JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew :androidApp:assembleDebug`
- KMP Android install: `~/Library/Android/sdk/platform-tools/adb install -r multiplatform/androidApp/build/outputs/apk/debug/androidApp-debug.apk`
- KMP Android release: `cd multiplatform && JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew :androidApp:bundleRelease` (produces AAB for Play Store)
- KMP Android publish to Play Internal Testing: `cd multiplatform && JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew :androidApp:publishReleaseBundle` (requires `play-service-account.json`)
- KMP iOS framework: `cd multiplatform && JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew :shared:linkDebugFrameworkIosSimulatorArm64`
- KMP iOS Xcode: `cd multiplatform/iosApp && xcodegen generate && open iosApp.xcodeproj`
- KMP iOS TestFlight: `cd multiplatform/iosApp && xcodegen generate && xcodebuild -scheme iosApp -sdk iphoneos -configuration Release -archivePath /tmp/KMP-ER.xcarchive archive && xcodebuild -exportArchive -archivePath /tmp/KMP-ER.xcarchive -exportOptionsPlist /tmp/KMP-ExportOptions.plist -exportPath /tmp/KMP-ERExport -allowProvisioningUpdates -authenticationKeyPath ~/.appstoreconnect/private_keys/AuthKey_8YM9M9P47X.p8 -authenticationKeyID 8YM9M9P47X -authenticationKeyIssuerID e5829743-777b-4a9f-a968-30a8714fb272`
- Android emulator: `~/Library/Android/sdk/emulator/emulator -avd Pixel_API_35 &`
- Deploy to Railway: `railway up --detach` (from project root)

## Architecture
- KMP Compose Multiplatform (iOS + Android) → FastAPI gateway → Claude Sonnet/Haiku hybrid API
- Free tier: 5 lenses (2 Sonnet "Wise" at indices 1,9 + 3 Haiku), 3 submissions/month
- Pro ($9.99/mo): All 20 base lenses on Sonnet, 50/day, no ads, history saved
- Voice Packs ($4.99 each, non-consumable IAP): 4 packs × 5 voices (indices 20-39), all Sonnet
  - Strategists (20-24), Revolutionaries (25-29), Philosophers (30-34), Creators (35-39)
  - Pack voices append after base takes in the doom scroll
- PostgreSQL for users/takes, Redis for rate limiting (optional, degrades gracefully)
- SSE streaming for real-time take delivery
- xcodegen for Xcode project generation (project.yml → .xcodeproj)

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
- PostgreSQL 16 + Redis via Homebrew (not Docker)

### CLI Publishing (both platforms — no GUI needed)
- **iOS → TestFlight**: App Store Connect API key `8YM9M9P47X` at `~/.appstoreconnect/private_keys/AuthKey_8YM9M9P47X.p8`, Issuer `e5829743-777b-4a9f-a968-30a8714fb272` — `xcodebuild archive + exportArchive` with auth flags (see Key Commands). Bundle ID: `com.endlessrumination.EndlessRumination`. ExportOptions plist at `/tmp/KMP-ExportOptions.plist` (method: app-store-connect, teamID: R6N5B4SDWH, destination: upload, signingStyle: automatic).
- **Android → Google Play Internal Testing**: Google Cloud service account (`play-service-account.json` in `multiplatform/`, gitignored) linked via Google Play Console Users & Permissions — `./gradlew publishReleaseBundle` builds signed AAB + uploads to internal track
- **Google Play Console**: Account ID `6253718630117210435`, app package `com.endlessrumination`, developer identity verification pending (draft releases only until verified)
- **Google Cloud project**: `endless-rumination` — Android Publisher API enabled, service account created and linked to Play Console

## Important Files
- `KICKOFF.md` — Complete project spec, read this FIRST
- `reference/mockup.jsx` — React prototype with exact design specs (DO NOT build React, extract design only)
- `reference/sample_takes.json` — Quality bar for AI-generated takes
- `backend/app/lenses/definitions.py` — Base 20 lens system prompts (indices 0-19)
- `backend/app/lenses/voice_packs.py` — Voice pack definitions (indices 20-39, 4 packs × 5 voices)
- `ios/` — Archived SwiftUI reference code (no longer primary)
- `railway.toml` — Railway deployment config
- `multiplatform/shared/src/commonMain/kotlin/.../App.kt` — Root composable with AnimatedContent navigation + overlay management
- `multiplatform/shared/src/commonMain/kotlin/.../AppState.kt` — State management (mutableStateOf, screen enum, take list, pro/shop flags)
- `multiplatform/shared/src/commonMain/kotlin/.../ApiClient.kt` — Ktor HTTP + SSE streaming (generateBatch returns Flow<Take>)
- `multiplatform/shared/src/commonMain/kotlin/.../theme/` — ERColors.kt + ERTypography.kt (full design system)
- `multiplatform/shared/src/commonMain/kotlin/.../model/` — Take, Lens (20 base), VoicePack (4×5 voices), User DTOs
- `multiplatform/shared/src/commonMain/kotlin/.../ui/` — All 11 screens (Splash, ProblemInput, Loading, Takes, TakeCard, Shop, PackDetail, ProUpgrade, SafetyOverlay, InstructionOverlay, AdBanner)
- `multiplatform/shared/src/commonMain/kotlin/.../service/SafetyService.kt` — Client blocklist + server safety check
- `multiplatform/shared/src/commonMain/kotlin/.../service/BillingModels.kt` — Shared billing types, sealed classes, product IDs
- `multiplatform/shared/src/commonMain/kotlin/.../service/BillingService.kt` — expect/actual billing abstraction (Google Play Billing + StoreKit 2)
- `multiplatform/iosApp/iosApp/StoreKitBridge.swift` — Swift StoreKit 2 bridge callable from Kotlin/Native
- `multiplatform/iosApp/iosApp/AdBannerBridge.swift` — Swift Google Mobile Ads bridge (GADBannerView wrapper)
- `backend/app/services/receipt_validator.py` — Abstract receipt validation base
- `backend/app/services/apple_validator.py` — App Store Server API v2 validation
- `backend/app/services/google_validator.py` — Google Play Developer API validation
- `multiplatform/androidApp/` — Android app module (Compose)
- `multiplatform/iosApp/` — iOS KMP wrapper (SwiftUI host for Compose views)
- `multiplatform/gradle/libs.versions.toml` — KMP version catalog (Kotlin 2.1.20, Compose 1.7.3, Ktor 3.1.1)

## Conventions
- Swift: SwiftUI only, iOS 17+, @Observable (not Combine), no UIKit unless necessary, no third-party UI deps
- Python: FastAPI, async everywhere, type hints, Pydantic models, `from __future__ import annotations` (Python 3.9 compat)
- All lens system prompts end with the standard format instruction (see KICKOFF.md)
- Color values defined in KICKOFF.md are authoritative — match exactly
- API cost: ~$0.013/free submission (2 Sonnet + 3 Haiku), ~$0.12/Pro submission (20 Sonnet), ~$0.025 per pack (5 Sonnet)
- "Wise" badge on Sonnet takes (including all pack voices), "Quick take · Powered by Haiku" on Haiku takes
- Triple-tap Shop button in DEBUG builds to toggle Pro status (simulator cheat)
- Voice pack indices 20-39 extend the base lens system; `Lens.displayInfo(index)` provides unified lookup
- Kotlin/KMP: State-based nav (AppScreen enum + `when`), AppState as plain class with `mutableStateOf`, explicit parameter passing (no CompositionLocal), Material Icons replace SF Symbols

## Android Distribution (Google Play Internal Testing)
Google Play Internal Testing is the Android equivalent of TestFlight. Uses `gradle-play-publisher` plugin for CLI uploads. **Full CLI pipeline verified and working.**

**Setup (all complete):**
1. Release keystore at `multiplatform/release.keystore` (gitignored), credentials in `multiplatform/keystore.properties` (gitignored)
2. `gradle-play-publisher` plugin (`com.github.triplet.play:3.11.0`) configured in `androidApp/build.gradle.kts`
3. Play Console: app `com.endlessrumination` created, Internal Testing track set up with initial AAB upload
4. Google Cloud: `endless-rumination` project, Android Publisher API enabled, service account created
5. Service account linked to Play Console via Users & Permissions (not Setup → API access, which no longer exists)
6. Service account JSON key at `multiplatform/play-service-account.json` (gitignored)

**CLI publish flow:**
- `cd multiplatform && JAVA_HOME=... ./gradlew publishReleaseBundle` — builds signed AAB + uploads to internal testing
- Currently creates draft releases (`ReleaseStatus.DRAFT`) due to pending developer identity verification
- Once verified: change to `ReleaseStatus.COMPLETED` in `androidApp/build.gradle.kts` for auto-rollout to testers
- Testers get notified in Play Store → install/update via normal Play Store flow
- No "Install from unknown sources" needed, auto-updates work
- Remember to bump `versionCode` in `androidApp/build.gradle.kts` before each publish (currently at 5)

## Monetization (IAP + Ads + Backend Validation)

### Billing (expect/actual pattern)
- **Common**: `BillingModels.kt` (shared types), `BillingService.kt` (expect class), `ActivityProvider.kt` (expect composable)
- **Android**: Google Play Billing Library v7 (`billing-ktx`). `BillingService.android.kt` handles products, purchases, acknowledgment. `ActivityProvider.android.kt` provides Activity context.
- **iOS**: StoreKit 2 via Swift bridge. `BillingService.ios.kt` delegates to `StoreKitBridgeProtocol`. `StoreKitBridge.swift` in `iosApp/` wraps async StoreKit 2 APIs with completion handlers callable from Kotlin/Native.
- **AppState** implements `BillingCallback` — receives purchase state changes, manages `isPro`, `ownedPackIDs`
- **App.kt** lifecycle: `LaunchedEffect` → `initialize()` + `loadProducts()` + `restorePurchases()`; `DisposableEffect` → `dispose()`
- Product IDs: `com.endlessrumination.pro.monthly` (subscription), `com.endlessrumination.pack.{strategists,revolutionaries,philosophers,creators}` (one-time)

### AdMob (real IDs on both platforms)
- **Common**: `PlatformAdBanner.kt` (expect composable), `AdBannerView.kt` (wrapper with chrome, "Remove" → paywall)
- **Android**: `PlatformAdBanner.android.kt` — `AndroidView` wrapping `AdView`, ad unit `ca-app-pub-5300605522420042/6942754502`
- **iOS**: `PlatformAdBanner.ios.kt` — `UIKitView` with `AdBannerProvider` factory lambda → `AdBannerBridge.swift` (`AdBannerWrapperView` wrapping `GADBannerView`), ad unit `ca-app-pub-5300605522420042/1359255336`
- **iOS SDK**: Google Mobile Ads 11.13.0 via SPM (`project.yml` packages section)
- **AndroidManifest.xml**: AdMob app ID `ca-app-pub-5300605522420042~5657592998`
- **iOS Info.plist**: `GADApplicationIdentifier` = `ca-app-pub-5300605522420042~6341428784`, plus SKAdNetwork IDs
- **iOS bridge pattern**: `AdBannerProvider.shared.createBanner` factory set in `iOSApp.swift` init, returns `AdBannerWrapperView` (UIView subclass that auto-finds rootViewController via responder chain)
- Banner shown on TakesScreen when `!isPro`, 50dp height

### Backend Receipt Validation
- **`POST /api/v1/subscription/verify-receipt`** — routes to Apple or Google validator by `platform` field
- **Apple**: App Store Server API v2 with JWT auth (.p8 key) → GET signed transaction → decode JWS → extract productId/expiry
- **Google**: Google Play Developer API with service account → `subscriptionsv2.get` / `products.get`
- Config: `apple_key_id`, `apple_issuer_id`, `apple_private_key_path`, `google_play_service_account_json` in Settings
- Updates user `subscription_tier` (pro) or `owned_pack_ids` (comma-separated) in DB
- Client calls `ApiClient.verifyReceipt()` after each successful purchase (background, non-blocking)
- 7 new backend tests in `test_subscription.py` (mocked validators)

## Multiplatform Stack
- Kotlin 2.1.20 + Compose Multiplatform 1.7.3 + AGP 8.7.3 + Gradle 8.11.1
- Ktor 3.1.1 (OkHttp engine Android, Darwin engine iOS) for HTTP + SSE
- Kotlinx.serialization 1.8.0 for JSON, Kotlinx.coroutines 1.10.1 for async
- Android: min SDK 26, target SDK 35, bundle ID `com.endlessrumination`
- KMP iOS: bundle ID `com.endlessrumination.EndlessRumination`, requires `CADisableMinimumFrameDurationOnPhone` in Info.plist
- Google Mobile Ads SDK 11.13.0 (iOS via SPM, Android via play-services-ads 23.6.0)
- Requires JAVA_HOME pointing to OpenJDK 17 (`/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home`)

## What NOT to Do
- Don't build a React/web app
- Don't use UIKit storyboards
- Don't hardcode API keys — use environment variables
- Don't persist free-tier takes to database
- Don't skip the safety check before generating takes
- Don't commit .xcodeproj — it's generated by xcodegen and gitignored
- Don't commit .venv or .env
