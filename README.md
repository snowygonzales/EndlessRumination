# Endless Rumination

> Doom-scroll your worries through AI perspectives that fade forever.

A psychology app with two native frontends — **SwiftUI** (iOS) and **Jetpack Compose** (Android) — backed by a **FastAPI** gateway to Claude AI. Users describe a problem, then scroll through AI-generated "takes" from radically different personas — comedian, stoic philosopher, therapist, your dog, and more. Each take fades forever on scroll unless the user is a Pro subscriber.

**Free tier**: 5 lenses (2 Sonnet "Wise" + 3 Haiku), 3 submissions/month, ads.
**Pro ($9.99/mo)**: All 20 base lenses on Sonnet, no ads, history saved.
**Voice Packs ($4.99 each)**: 4 packs of 5 historical-figure voices (indices 20-39), all Sonnet.

## Status

| Component | Status |
|-----------|--------|
| Backend (FastAPI) | Live on Railway |
| iOS App (SwiftUI) | Complete, on TestFlight |
| Android App (Compose) | Complete, on Google Play Internal Testing |
| Voice Pack Shop | 4 packs implemented (Strategists, Revolutionaries, Philosophers, Creators) |
| AdMob | Real ads on both platforms |
| IAP | StoreKit 2 (iOS) + Google Play Billing v7 (Android) |

**Production API**: `https://backend-production-5537.up.railway.app`

## Quick Start

### Prerequisites

- macOS with Xcode 16+ (iOS development)
- JDK 17 + Android SDK (Android development)
- Python 3.9+ (backend)
- PostgreSQL and Redis (backend, local dev) — or use Docker
- [xcodegen](https://github.com/yonaskolb/XcodeGen) (`brew install xcodegen`)

### Backend (local dev)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env → set ANTHROPIC_API_KEY from console.anthropic.com

# Start PostgreSQL + Redis, then:
uvicorn app.main:app --reload

# Verify
curl http://localhost:8000/health
```

### Backend (Docker)

```bash
cd backend
cp .env.example .env
# Edit .env → set ANTHROPIC_API_KEY
docker-compose up -d
```

### iOS App

```bash
cd ios
xcodegen generate
open EndlessRumination.xcodeproj
# Build & run on simulator (Cmd+R)
```

The debug build connects to `localhost:8000`. Release builds point to the Railway production URL.

### Android App

```bash
cd android
JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew :app:assembleDebug
# Install on emulator/device:
~/Library/Android/sdk/platform-tools/adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Android always connects to the Railway production URL.

### Tests

```bash
# Backend (42 tests, SQLite + mocked Claude API, no Docker needed)
cd backend && pytest -v

# iOS (9 tests via Xcode test runner)
# Cmd+U in Xcode
```

## Project Structure

```
EndlessRumination/
├── KICKOFF.md                 ← Full project spec
├── CLAUDE.md                  ← Claude Code instructions
├── railway.toml               ← Railway deployment config
├── docs/
│   ├── privacy-policy.md      ← App Store privacy policy
│   └── support.md             ← Support page
├── reference/
│   ├── mockup.jsx             ← React prototype (design reference only)
│   └── sample_takes.json      ← 20 sample AI takes (quality bar)
├── backend/
│   ├── app/
│   │   ├── main.py            ← FastAPI app, health check, CORS
│   │   ├── config.py          ← Settings via env vars
│   │   ├── models/            ← Pydantic schemas + SQLAlchemy models
│   │   ├── routers/           ← auth, safety, takes, subscription
│   │   ├── services/          ← Claude API, safety, rate limiting, auth, receipt validation
│   │   └── lenses/            ← 20 base persona prompts + 4 voice packs (20 voices)
│   ├── tests/                 ← 42 tests (pytest)
│   ├── Dockerfile
│   └── requirements.txt
├── ios/                       ← SwiftUI native iOS app
│   ├── project.yml            ← xcodegen config (generates .xcodeproj)
│   └── EndlessRumination/
│       ├── App/               ← App entry point + @Observable state machine
│       ├── Theme/             ← Colors, typography, animations
│       ├── Models/            ← Lens, Take, VoicePack, User
│       ├── Services/          ← APIClient (SSE), SubscriptionManager (StoreKit 2), SafetyService
│       ├── Views/             ← All SwiftUI screens + real AdMob banner
│       ├── Assets.xcassets/   ← App icon + accent color
│       └── Info.plist         ← AdMob IDs, SKAdNetwork, ATS config
├── android/                   ← Jetpack Compose native Android app
│   ├── app/
│   │   ├── build.gradle.kts   ← Compose BOM, Ktor, billing, ads, signing
│   │   └── src/main/kotlin/
│   │       └── com/endlessrumination/
│   │           ├── App.kt          ← Root composable, navigation, billing lifecycle
│   │           ├── AppState.kt     ← ViewModel state management
│   │           ├── ApiClient.kt    ← Ktor HTTP + SSE streaming
│   │           ├── model/          ← Lens, Take, VoicePack, User
│   │           ├── service/        ← BillingService, HapticService, SafetyService
│   │           ├── ui/             ← All Compose screens + real AdMob banner
│   │           └── theme/          ← ERColors, ERTypography
│   └── gradle/                ← Gradle wrapper
└── multiplatform/             ← ARCHIVED (KMP reference code only)
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/lenses` | List all 20 lens personas |
| `POST` | `/api/v1/safety-check` | Screen user input before generation |
| `POST` | `/api/v1/generate-take` | Generate a single take from one lens |
| `POST` | `/api/v1/generate-batch` | Batch generate takes via SSE stream |
| `POST` | `/api/v1/auth/register` | Register by device ID, returns JWT |
| `POST` | `/api/v1/auth/login` | Login by device ID, returns JWT |
| `GET` | `/api/v1/subscription/status` | Tier + daily usage (auth required) |
| `POST` | `/api/v1/subscription/verify-receipt` | Validate Apple/Google purchase receipt |
| `GET` | `/api/v1/takes/history` | Saved takes history (Pro only) |

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | **Yes** | — | From console.anthropic.com |
| `DATABASE_URL` | No | `postgresql+asyncpg://...localhost.../endless_rumination` | PostgreSQL connection |
| `REDIS_URL` | No | `redis://localhost:6379` | Redis (rate limiting degrades gracefully without it) |
| `JWT_SECRET` | Production | `change-me-in-production` | JWT signing secret |
| `DEBUG` | No | `false` | Enable debug logging |

## Monetization

| Tier | Lenses | AI Model | Submissions | Ads | Price |
|------|--------|----------|-------------|-----|-------|
| Free | 5 (indices 0-4) | 2 Sonnet "Wise" (1,9) + 3 Haiku | 1/day, 3/month | Yes | Free |
| Pro | All 20 | Sonnet | 50/day | No | $9.99/mo |
| Voice Packs | 5 per pack | Sonnet | Same as tier | Same as tier | $4.99 each |

- 4 Voice Packs: Strategists (20-24), Revolutionaries (25-29), Philosophers (30-34), Creators (35-39)
- "Wise" badge on Sonnet takes, "Quick take · Powered by Haiku" on Haiku takes
- Triple-tap Shop button in DEBUG builds to toggle Pro status

## Cost

| Item | Cost |
|------|------|
| Apple Developer Program | $99/year |
| Google Play Developer | $25 one-time |
| Railway backend hosting | ~$5-15/month |
| Anthropic API — free submission | ~$0.013 (2 Sonnet + 3 Haiku + safety) |
| Anthropic API — Pro submission | ~$0.12 (20 Sonnet + safety) |
| Anthropic API — per voice pack | ~$0.025 (5 Sonnet) |
