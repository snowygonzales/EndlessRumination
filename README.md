# Endless Rumination

> Doom-scroll your worries through 20 AI perspectives that fade forever.

A native iOS psychology app (SwiftUI) with a Python backend (FastAPI). Users describe a problem, then scroll through AI-generated "takes" from 20 radically different personas — comedian, stoic philosopher, therapist, your dog, and more. Each take fades forever on scroll unless the user is a Pro subscriber.

## Getting Started

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (for PostgreSQL + Redis)
- An Anthropic API key

### Backend Setup

```bash
cd backend

# Copy env template and add your API key
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY

# Option A: Docker (recommended)
docker-compose up

# Option B: Local dev (requires Postgres + Redis running)
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Health check: `GET /health`.

### Running Tests

```bash
cd backend
pytest -v
```

## Project Structure

```
├── KICKOFF.md              ← Full project spec
├── CLAUDE.md               ← Claude Code configuration
├── reference/
│   ├── mockup.jsx          ← React prototype (design reference only)
│   └── sample_takes.json   ← 20 sample AI takes (quality reference)
├── backend/
│   ├── app/
│   │   ├── main.py         ← FastAPI app + health check
│   │   ├── config.py       ← Pydantic settings (env vars)
│   │   ├── models/         ← Pydantic schemas + SQLAlchemy models
│   │   ├── routers/        ← API endpoints (auth, safety, takes, subscription)
│   │   ├── services/       ← Claude API, safety check, rate limiter, auth
│   │   └── lenses/         ← 20 persona system prompts (source of truth)
│   ├── tests/              ← pytest suite (21 tests)
│   ├── alembic/            ← DB migrations
│   ├── docker-compose.yml  ← API + Postgres + Redis
│   ├── Dockerfile
│   └── requirements.txt
└── ios/                    ← SwiftUI app (Phase 2)
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/lenses` | List all 20 lens personas (metadata only) |
| `POST` | `/api/v1/safety-check` | Screen user input before generation |
| `POST` | `/api/v1/generate-take` | Generate a single take from one lens |
| `POST` | `/api/v1/generate-batch` | Batch generate takes (SSE stream) |
| `POST` | `/api/v1/auth/register` | Register by device ID |
| `POST` | `/api/v1/auth/login` | Login by device ID |
| `GET` | `/api/v1/subscription/status` | Get tier + usage info |
| `GET` | `/api/v1/takes/history` | Take history (Pro only) |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key |
| `DATABASE_URL` | No | PostgreSQL connection (default: localhost) |
| `REDIS_URL` | No | Redis connection (default: localhost) |
| `JWT_SECRET` | Yes (prod) | JWT signing secret |
| `APPLE_SHARED_SECRET` | No | StoreKit receipt validation (Phase 3) |

## Build Order
1. **Backend Core** — FastAPI + Claude streaming + safety check *(done)*
2. **iOS Core** — SwiftUI screens + API client + swipe mechanics
3. **Monetization** — StoreKit 2 + ads + rate limiting + history
4. **Polish** — Haptics, onboarding, App Store prep
