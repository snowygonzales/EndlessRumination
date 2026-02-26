# CLAUDE.md — Endless Rumination

## Project Overview
Psychology app (SwiftUI iOS + KMP multiplatform) + Python backend (FastAPI). Users describe a problem, then doom-scroll through AI-generated perspectives from different personas. Each perspective fades forever unless user is a Pro subscriber. Base lenses (0-19) come with free/Pro tiers; purchasable Voice Packs (20-39) add 5 historical-figure voices each.

**Multiplatform (in progress):** KMP + Compose Multiplatform scaffold in `multiplatform/` targets both iOS and Android from shared Kotlin code. The original SwiftUI app in `ios/` remains the production iOS app on TestFlight.

## Key Commands
- Backend (local): `cd backend && source .venv/bin/activate && uvicorn app.main:app --reload`
- Backend (Docker): `cd backend && docker-compose up`
- Backend tests: `cd backend && pytest -v` (35 tests, SQLite + mocked Claude)
- iOS project: `cd ios && xcodegen generate && open EndlessRumination.xcodeproj`
- iOS tests: Cmd+U in Xcode (9 tests)
- KMP Android: `cd multiplatform && JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew :androidApp:assembleDebug`
- KMP iOS framework: `cd multiplatform && JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew :shared:linkDebugFrameworkIosSimulatorArm64`
- KMP iOS Xcode: `cd multiplatform/iosApp && xcodegen generate && open iosApp.xcodeproj`
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

## Live Infrastructure
- **Production API**: https://backend-production-5537.up.railway.app
- **Railway dashboard**: https://railway.com/project/30951286-357e-4529-a21c-bb527d62eb13
- **Privacy policy**: https://github.com/snowygonzales/EndlessRumination/blob/master/docs/privacy-policy.md
- **Support page**: https://github.com/snowygonzales/EndlessRumination/blob/master/docs/support.md
- iOS debug builds → localhost:8000, release builds → Railway URL

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
- `multiplatform/shared/src/commonMain/` — Shared KMP Compose UI + Ktor API client
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
- Voice pack indices 20-39 extend the base lens system; `Lens.displayInfo(at:)` provides unified lookup

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
