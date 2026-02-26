# CLAUDE.md — Endless Rumination

## Project Overview
Psychology app (SwiftUI iOS + KMP multiplatform) + Python backend (FastAPI). Users describe a problem, then doom-scroll through AI-generated perspectives from different personas. Each perspective fades forever unless user is a Pro subscriber. Base lenses (0-19) come with free/Pro tiers; purchasable Voice Packs (20-39) add 5 historical-figure voices each.

**Multiplatform:** KMP + Compose Multiplatform in `multiplatform/` targets both iOS and Android from shared Kotlin code. All 11 screens ported from SwiftUI to shared Compose (splash, input, loading, takes doom-scroll, shop, pack detail, pro paywall, safety overlay, instruction overlay, ad banner, take card). IAP stubbed with triple-tap debug toggle. The original SwiftUI app in `ios/` remains the production iOS app on TestFlight.

## Key Commands
- Backend (local): `cd backend && source .venv/bin/activate && uvicorn app.main:app --reload`
- Backend (Docker): `cd backend && docker-compose up`
- Backend tests: `cd backend && pytest -v` (35 tests, SQLite + mocked Claude)
- iOS project: `cd ios && xcodegen generate && open EndlessRumination.xcodeproj`
- iOS tests: Cmd+U in Xcode (9 tests)
- KMP Android build: `cd multiplatform && JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew :androidApp:assembleDebug`
- KMP Android install: `~/Library/Android/sdk/platform-tools/adb install -r multiplatform/androidApp/build/outputs/apk/debug/androidApp-debug.apk`
- KMP Android release: `cd multiplatform && JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew :androidApp:bundleRelease` (produces AAB for Play Store)
- KMP iOS framework: `cd multiplatform && JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew :shared:linkDebugFrameworkIosSimulatorArm64`
- KMP iOS Xcode: `cd multiplatform/iosApp && xcodegen generate && open iosApp.xcodeproj`
- Android emulator: `~/Library/Android/sdk/emulator/emulator -avd Pixel_API_35 &`
- TestFlight upload: `cd ios && xcodegen generate && xcodebuild -scheme EndlessRumination -sdk iphoneos -configuration Release -archivePath /tmp/ER.xcarchive archive && xcodebuild -exportArchive -archivePath /tmp/ER.xcarchive -exportOptionsPlist /tmp/ExportOptions.plist -exportPath /tmp/ERExport -allowProvisioningUpdates -authenticationKeyPath ~/.appstoreconnect/private_keys/AuthKey_8YM9M9P47X.p8 -authenticationKeyID 8YM9M9P47X -authenticationKeyIssuerID e5829743-777b-4a9f-a968-30a8714fb272`
- Deploy to Railway: `railway up --detach` (from project root)

## Architecture
- SwiftUI iOS 17+ app → FastAPI gateway → Claude Sonnet/Haiku hybrid API
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
- **App Store Connect API**: Key `8YM9M9P47X` at `~/.appstoreconnect/private_keys/AuthKey_8YM9M9P47X.p8`, Issuer `e5829743-777b-4a9f-a968-30a8714fb272` — enables CLI TestFlight uploads (no Xcode Organizer needed)
- **Production API**: https://backend-production-5537.up.railway.app
- **Railway dashboard**: https://railway.com/project/30951286-357e-4529-a21c-bb527d62eb13
- **Privacy policy**: https://github.com/snowygonzales/EndlessRumination/blob/master/docs/privacy-policy.md
- **Support page**: https://github.com/snowygonzales/EndlessRumination/blob/master/docs/support.md
- iOS debug builds → localhost:8000, release builds → Railway URL
- PostgreSQL 16 + Redis via Homebrew (not Docker)

## Important Files
- `KICKOFF.md` — Complete project spec, read this FIRST
- `reference/mockup.jsx` — React prototype with exact design specs (DO NOT build React, extract design only)
- `reference/sample_takes.json` — Quality bar for AI-generated takes
- `backend/app/lenses/definitions.py` — Base 20 lens system prompts (indices 0-19)
- `backend/app/lenses/voice_packs.py` — Voice pack definitions (indices 20-39, 4 packs × 5 voices)
- `ios/EndlessRumination/Models/VoicePack.swift` — iOS voice pack model with all pack/voice data
- `ios/EndlessRumination/Views/ShopView.swift` — Voice Pack Shop UI
- `ios/project.yml` — xcodegen config (source of truth for Xcode project)
- `railway.toml` — Railway deployment config
- `multiplatform/shared/src/commonMain/kotlin/.../App.kt` — Root composable with AnimatedContent navigation + overlay management
- `multiplatform/shared/src/commonMain/kotlin/.../AppState.kt` — State management (mutableStateOf, screen enum, take list, pro/shop flags)
- `multiplatform/shared/src/commonMain/kotlin/.../ApiClient.kt` — Ktor HTTP + SSE streaming (generateBatch returns Flow<Take>)
- `multiplatform/shared/src/commonMain/kotlin/.../theme/` — ERColors.kt + ERTypography.kt (full design system)
- `multiplatform/shared/src/commonMain/kotlin/.../model/` — Take, Lens (20 base), VoicePack (4×5 voices), User DTOs
- `multiplatform/shared/src/commonMain/kotlin/.../ui/` — All 11 screens (Splash, ProblemInput, Loading, Takes, TakeCard, Shop, PackDetail, ProUpgrade, SafetyOverlay, InstructionOverlay, AdBanner)
- `multiplatform/shared/src/commonMain/kotlin/.../service/SafetyService.kt` — Client blocklist + server safety check
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

## Android Distribution (Firebase App Distribution)
Firebase App Distribution is the Android equivalent of TestFlight — distributes debug/release APKs to testers without the Play Store. Setup:
1. Create Firebase project at https://console.firebase.google.com
2. Add Android app (`com.endlessrumination`), download `google-services.json` → `multiplatform/androidApp/`
3. Install Firebase CLI: `npm install -g firebase-tools && firebase login`
4. Distribute: `firebase appdistribution:distribute multiplatform/androidApp/build/outputs/apk/debug/androidApp-debug.apk --app <firebase-app-id> --groups "testers"`
5. Testers get email invite, install via Firebase App Tester app on their Android device
- Alternative: Google Play Internal Testing track (requires Play Console account, $25 one-time, takes 1-2 days initial review)
- Quick alternative: share APK directly via link (debug APK, testers enable "Install from unknown sources")

## Multiplatform Stack
- Kotlin 2.1.20 + Compose Multiplatform 1.7.3 + AGP 8.7.3 + Gradle 8.11.1
- Ktor 3.1.1 (OkHttp engine Android, Darwin engine iOS) for HTTP + SSE
- Kotlinx.serialization 1.8.0 for JSON, Kotlinx.coroutines 1.10.1 for async
- Android: min SDK 26, target SDK 35, bundle ID `com.endlessrumination`
- KMP iOS: bundle ID `com.endlessrumination.kmp`, requires `CADisableMinimumFrameDurationOnPhone` in Info.plist
- Requires JAVA_HOME pointing to OpenJDK 17 (`/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home`)

## What NOT to Do
- Don't build a React/web app
- Don't use UIKit storyboards
- Don't hardcode API keys — use environment variables
- Don't persist free-tier takes to database
- Don't skip the safety check before generating takes
- Don't commit .xcodeproj — it's generated by xcodegen and gitignored
- Don't commit .venv or .env
