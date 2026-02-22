# Endless Rumination

> Doom-scroll your worries through AI perspectives that fade forever.

A native iOS psychology app (SwiftUI) with a Python backend (FastAPI). Users describe a problem, then scroll through AI-generated "takes" from radically different personas — comedian, stoic philosopher, therapist, your dog, and more. Each take fades forever on scroll unless the user is a Pro subscriber.

**Free tier**: 5 lenses (2 Sonnet "Wise" + 3 Haiku), 3 submissions/month, ads.
**Pro ($9.99/mo)**: All 20 lenses on Sonnet, no ads, history saved.

## Status

| Component | Status |
|-----------|--------|
| Backend (FastAPI) | Live on Railway |
| iOS App (SwiftUI) | Complete, simulator-tested |
| App Icon | Done (1024x1024 gradient infinity) |
| Privacy Policy | Hosted on GitHub |
| TestFlight | Pending (see `TESTFLIGHT_TODO.md`) |

**Production API**: `https://backend-production-5537.up.railway.app`

## Quick Start

### Prerequisites

- macOS with Xcode 16+ (iOS development)
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

### Tests

```bash
# Backend (21 tests, SQLite + mocked Claude API, no Docker needed)
cd backend && pytest -v

# iOS (9 tests via Xcode test runner)
# Cmd+U in Xcode
```

## Project Structure

```
EndlessRumination/
├── KICKOFF.md                 ← Full project spec
├── CLAUDE.md                  ← Claude Code instructions
├── TESTFLIGHT_TODO.md         ← TestFlight readiness checklist
├── railway.toml               ← Railway deployment config
├── docs/
│   └── privacy-policy.md      ← App Store privacy policy
├── reference/
│   ├── mockup.jsx             ← React prototype (design reference only)
│   └── sample_takes.json      ← 20 sample AI takes (quality bar)
├── backend/
│   ├── app/
│   │   ├── main.py            ← FastAPI app, health check, CORS
│   │   ├── config.py          ← Settings via env vars
│   │   ├── models/
│   │   │   ├── schemas.py     ← Pydantic request/response models
│   │   │   └── database.py    ← SQLAlchemy async models
│   │   ├── routers/
│   │   │   ├── auth.py        ← POST /register, /login (device-based JWT)
│   │   │   ├── safety.py      ← POST /safety-check (Claude classification)
│   │   │   ├── takes.py       ← POST /generate-take, /generate-batch (SSE)
│   │   │   └── subscription.py← GET /status, POST /verify-receipt
│   │   ├── services/
│   │   │   ├── claude_service.py   ← Claude API (Sonnet/Haiku hybrid, parallel + SSE)
│   │   │   ├── safety_service.py   ← SAFE/UNSAFE classification
│   │   │   ├── rate_limiter.py     ← Redis daily counters (graceful without Redis)
│   │   │   └── auth_service.py     ← JWT create/decode
│   │   └── lenses/
│   │       └── definitions.py      ← All 20 persona system prompts
│   ├── tests/                 ← 21 tests (pytest)
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
└── ios/
    ├── project.yml            ← xcodegen config (generates .xcodeproj)
    └── EndlessRumination/
        ├── App/               ← App entry point + @Observable state machine
        ├── Theme/             ← Colors, typography, animations
        ├── Models/            ← Lens, Take, Problem, User
        ├── Services/          ← APIClient (SSE streaming), SafetyService
        ├── Views/             ← All SwiftUI screens
        ├── Assets.xcassets/   ← App icon + accent color
        └── Info.plist         ← ATS config for local networking
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
| `GET` | `/api/v1/takes/history` | Saved takes history (Pro only) |

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | **Yes** | — | From console.anthropic.com |
| `DATABASE_URL` | No | `postgresql+asyncpg://...localhost.../endless_rumination` | PostgreSQL connection |
| `REDIS_URL` | No | `redis://localhost:6379` | Redis (rate limiting degrades gracefully without it) |
| `JWT_SECRET` | Production | `change-me-in-production` | JWT signing secret |
| `DEBUG` | No | `false` | Enable debug logging |

## Monetization Model

| Tier | Lenses | AI Model | Submissions | Ads | Price |
|------|--------|----------|-------------|-----|-------|
| Free | 5 (indices 0-4) | 2 Sonnet "Wise" (1,9) + 3 Haiku | 1/day, 3/month | Yes | Free |
| Pro | All 20 | Sonnet | 50/day | No | $9.99/mo |

- "Wise" badge (sparkle icon) appears on Sonnet-powered takes
- "Quick take · Powered by Haiku" label on Haiku takes
- Triple-tap the PRO badge in simulator (DEBUG builds) to toggle Pro status

## Build Phases

1. **Backend Core** — FastAPI + Claude streaming + safety + auth + rate limiting ✅
2. **iOS Core** — SwiftUI screens + API client + SSE streaming + swipe mechanics ✅
3. **Deployment** — Railway backend + app icon + privacy policy ✅
4. **Monetization** — Sonnet/Haiku hybrid, tiered lenses, wise badges, Pro cheat ✅
5. **TestFlight** — Apple Developer account + App Store Connect + archive/upload *(next)*
6. **Polish** — StoreKit 2 subscriptions, ads SDK, haptics, onboarding

## Cost

| Item | Cost |
|------|------|
| Apple Developer Program | $99/year |
| Railway backend hosting | ~$5-15/month |
| Anthropic API — free user submission | ~$0.013 (2 Sonnet + 3 Haiku + safety) |
| Anthropic API — Pro user submission | ~$0.12 (20 Sonnet + safety) |
| TestFlight distribution | Free |
