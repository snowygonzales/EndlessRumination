# CLAUDE.md — Endless Rumination

## Project Overview
Native iOS psychology app (SwiftUI) + Python backend (FastAPI). Users describe a problem, then doom-scroll through 20 AI-generated perspectives from different personas. Each perspective fades forever unless user is a Pro subscriber.

## Key Commands
- Backend: `cd backend && uvicorn app.main:app --reload`
- iOS: Open `ios/EndlessRumination.xcodeproj` in Xcode
- Docker: `cd backend && docker-compose up`
- Tests: `cd backend && pytest` / Xcode test runner for iOS

## Architecture
- SwiftUI iOS app → FastAPI gateway → Claude Sonnet API
- PostgreSQL for users/takes, Redis for rate limiting
- SSE streaming for real-time take delivery

## Important Files
- `KICKOFF.md` — Complete project spec, read this FIRST
- `reference/mockup.jsx` — React prototype with exact design specs (DO NOT build React, extract design only)
- `reference/sample_takes.json` — Quality bar for AI-generated takes
- `backend/app/lenses/definitions.py` — All 20 lens system prompts (source of truth)

## Conventions
- Swift: SwiftUI only, iOS 17+, no UIKit unless necessary, no third-party UI deps
- Python: FastAPI, async everywhere, type hints, Pydantic models
- All lens system prompts end with the standard format instruction (see KICKOFF.md)
- Color values defined in KICKOFF.md are authoritative — match exactly

## What NOT to Do
- Don't build a React/web app — this is native iOS
- Don't use UIKit storyboards
- Don't hardcode API keys — use environment variables
- Don't persist free-tier takes to database
- Don't skip the safety check before generating takes
