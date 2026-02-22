# Endless Rumination

> Doom-scroll your worries through 20 AI perspectives that fade forever.

A native iOS psychology app (SwiftUI) with a Python backend (FastAPI). Users describe a problem, then scroll through AI-generated "takes" from 20 radically different personas — comedian, stoic philosopher, therapist, your dog, and more. Each take fades forever on scroll unless the user is a Pro subscriber.

## Quick Start (macOS)

You need a Mac for the full stack (Xcode is macOS-only).

```bash
# 1. Clone and set up environment
git clone https://github.com/snowygonzales/EndlessRumination.git
cd EndlessRumination/backend
cp .env.example .env
# Edit .env → set ANTHROPIC_API_KEY to your key from console.anthropic.com

# 2. Start backend (Docker)
docker-compose up -d

# 3. Verify API is running
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/lenses | python3 -m json.tool

# 4. Test a safety check + take generation
curl -X POST http://localhost:8000/api/v1/safety-check \
  -H "Content-Type: application/json" \
  -d '{"problem": "I bombed my job interview and sent an angry email to the recruiter"}'

curl -X POST http://localhost:8000/api/v1/generate-take \
  -H "Content-Type: application/json" \
  -d '{"problem": "I bombed my job interview and sent an angry email to the recruiter", "lens_index": 0}'

# 5. Open iOS app in Xcode (Phase 2)
open ios/EndlessRumination.xcodeproj
```

### Backend without Docker

If you prefer running locally (requires PostgreSQL and Redis installed):

```bash
cd backend
pip install -r requirements.txt
# Start Postgres and Redis separately, then:
uvicorn app.main:app --reload
```

### Running Tests

Tests use SQLite in-memory and mock the Claude API — no Docker needed.

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

## Project Structure

```
EndlessRumination/
├── KICKOFF.md                 ← Full project spec (start here)
├── CLAUDE.md                  ← Claude Code configuration
├── reference/
│   ├── mockup.jsx             ← React prototype (design reference only — DO NOT build React)
│   └── sample_takes.json      ← 20 sample AI takes (quality bar)
├── backend/                   ← Phase 1: COMPLETE
│   ├── app/
│   │   ├── main.py            ← FastAPI app, health check, CORS
│   │   ├── config.py          ← Settings via env vars (.env)
│   │   ├── models/
│   │   │   ├── schemas.py     ← Pydantic request/response models
│   │   │   └── database.py    ← SQLAlchemy async models (User, Problem, Take)
│   │   ├── routers/
│   │   │   ├── auth.py        ← POST /register, /login (device-based JWT)
│   │   │   ├── safety.py      ← POST /safety-check (Claude classification)
│   │   │   ├── takes.py       ← POST /generate-take, /generate-batch (SSE), GET /history
│   │   │   └── subscription.py← GET /status, POST /verify-receipt (stub)
│   │   ├── services/
│   │   │   ├── claude_service.py   ← Single + batch take generation (parallel, streaming)
│   │   │   ├── safety_service.py   ← SAFE/UNSAFE classification via Claude
│   │   │   ├── rate_limiter.py     ← Redis daily counters (takes + problems)
│   │   │   └── auth_service.py     ← JWT create/decode + FastAPI dependencies
│   │   └── lenses/
│   │       └── definitions.py      ← All 20 persona system prompts (source of truth)
│   ├── tests/                 ← 21 tests (pytest, mocked API + SQLite)
│   ├── alembic/               ← DB migration framework
│   ├── docker-compose.yml     ← API + PostgreSQL 16 + Redis 7
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example           ← Template — copy to .env and add your API key
│   └── .gitignore
└── ios/                       ← Phase 2: TODO
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/lenses` | List all 20 lens personas (metadata only) |
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
| `DATABASE_URL` | No | `postgresql+asyncpg://postgres:postgres@localhost:5432/endless_rumination` | PostgreSQL connection |
| `REDIS_URL` | No | `redis://localhost:6379` | Redis connection |
| `JWT_SECRET` | Production | `change-me-in-production` | JWT signing secret |
| `DEBUG` | No | `false` | Enable debug logging |

## Build Phases

1. **Backend Core** — FastAPI + Claude streaming + safety check + auth + rate limiting *(complete)*
2. **iOS Core** — SwiftUI screens + API client + SSE streaming + swipe mechanics *(next)*
3. **Monetization** — StoreKit 2 + ads + rate limiting + take history
4. **Polish** — Haptics, onboarding, App Store prep

## Development Notes

- Backend tests run without Docker (SQLite + mocked Claude API)
- The `.env` file is gitignored — never committed
- `reference/mockup.jsx` is the design bible — match colors, spacing, animations exactly
- `reference/sample_takes.json` shows the quality bar for each lens persona
- All 20 lenses are defined in `backend/app/lenses/definitions.py`
