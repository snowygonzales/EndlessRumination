# Mac Quick Start — Read This First

## 1. Clone & Setup

```bash
git clone https://github.com/snowygonzales/EndlessRumination.git
cd EndlessRumination
```

## 2. Backend

```bash
cd backend
cp .env.example .env
# EDIT .env — paste your NEW rotated Anthropic API key (old one was exposed)
```

Then start everything:

```bash
docker-compose up -d
```

Verify:

```bash
curl http://localhost:8000/health
# Should return: {"status":"ok","app":"Endless Rumination API"}
```

## 3. Tests

```bash
pip install -r requirements.txt
pytest -v
# All 21 tests should pass
```

## 4. What's Done (Phase 1)

- FastAPI backend: auth, safety check, take generation (single + batch SSE), rate limiting
- All 20 lens personas with system prompts
- Docker Compose: API + PostgreSQL + Redis
- 21 passing tests

## 5. What's Next (Phase 2 — iOS Core)

Build the SwiftUI app. Read KICKOFF.md for full spec, reference/mockup.jsx for exact design.

Prompt for Claude Code on Mac:

```
Read KICKOFF.md and CLAUDE.md, then build Phase 2: iOS Core.
Start with the Xcode project shell, then:
1. App shell with navigation (splash → input → loading → takes)
2. Problem input view with word counter
3. API client with SSE streaming support
4. Takes view with swipe gesture + fade animation
5. Safety overlay + client-side keyword check
6. Loading screen with progress
Match the design exactly from reference/mockup.jsx.
```

## Key Files to Know

- `KICKOFF.md` — Full project spec (colors, typography, animations, screen flow)
- `reference/mockup.jsx` — Design bible (DO NOT build React, extract design only)
- `reference/sample_takes.json` — Quality bar for AI output
- `backend/app/lenses/definitions.py` — All 20 lens system prompts
- `backend/.env` — Your API key goes here (gitignored)

## Env Vars Needed

Only one is required: `ANTHROPIC_API_KEY` in `backend/.env`

Everything else has working defaults for local dev via Docker.

## Rotate Your API Key

The old key was exposed in conversation context. Go to:
https://console.anthropic.com/settings/keys
Revoke old → create new → paste in backend/.env
