# Endless Rumination — Claude Code Project Kickoff

## What You're Building

A native iOS app (SwiftUI, no JavaScript/React Native) called **Endless Rumination**. It's a psychology-meets-doom-scrolling app where users describe a problem, then scroll through AI-generated "takes" — each from a radically different persona (comedian, stoic philosopher, therapist, your dog, etc). Each take fades forever on scroll unless the user is a Pro subscriber.

## Reference Mockup

See `reference/mockup.jsx` — this is a working React prototype that demonstrates the exact UX flow, visual design, animations, all 20 lens personas, and sample AI-generated takes. Use it as the source of truth for:
- Color palette, typography, spacing
- Screen flow and transitions
- Card layout and fade mechanics
- Ad banner placement and Pro upsell UX
- Word counter behavior
- Safety rejection overlay

**DO NOT** build a React app. This reference is for design/UX extraction only. Build native SwiftUI.

---

## Architecture Overview

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  SwiftUI    │────▶│  API Gateway     │────▶│  Claude API     │
│  iOS App    │◀────│  (FastAPI/Python) │◀────│  (Sonnet)       │
└─────────────┘     └──────────────────┘     └─────────────────┘
                           │
                    ┌──────┴──────┐
                    │  PostgreSQL │  (users, problems, takes for Pro)
                    │  + Redis    │  (rate limiting, session cache)
                    └─────────────┘
```

### Component Breakdown

**1. iOS App (SwiftUI)** — `ios/` directory
- Minimum target: iOS 17
- SwiftUI only, no UIKit wrappers unless absolutely necessary
- No third-party dependencies for core UI (StoreKit 2 for IAP is fine)

**2. API Gateway (FastAPI)** — `backend/` directory
- Python 3.11+ with FastAPI
- Handles: auth, safety screening, rate limiting, Claude API proxy, take storage for Pro users
- Deployed via Docker

**3. Claude API Integration**
- Model: `claude-sonnet-4-20250514` (Sonnet for cost efficiency)
- Each lens has a dedicated system prompt (see Lens Definitions below)
- Streaming responses back to the client for perceived speed

---

## Screen Flow

### Screen 1: Splash
- App logo (∞ symbol in gradient square), app name "Endless Rumination", tagline "Scroll your worries"
- Single "Begin" button
- Show on first launch and cold start only

### Screen 2: Problem Input
- Header: "What's on your mind?" + PRO badge (gold gradient)
- Subtext: "Describe what's bothering you. Be specific..."
- Large text area with placeholder "I can't stop thinking about..."
- Live word counter bottom-right: `{count} / 20 words` — changes color as threshold approaches (dim → gold at 15 → green at 20)
- Submit button: disabled state until 20 words, then activates with warm gradient
- Footer: safety disclaimer text
- Safety rejection: full-screen overlay with shield icon, explanation, crisis resource link, "Edit my input" button

### Screen 3: Loading
- Spinner + "Generating perspectives..."
- Transition to takes as soon as first take streams in (don't wait for all 20)

### Screen 4: Takes (Doom Scroll)
- Header: "← New problem" button (left) + take counter `{n} / 20` (right)
- Full-screen take card with:
  - Lens badge (emoji + name, colored pill)
  - Headline (serif font, ~24pt)
  - Body text (sans-serif, 13.5pt, secondary color)
- Swipe-up gesture advances to next take
- Previous take fades out upward with "gone forever" flash
- Instruction overlay on first view: "Swipe up for next take / Each perspective disappears forever / Free: 10 takes/day · Pro: unlimited"
- Bottom: Ad banner (50pt height) with "Remove" upsell link
- Free tier: 10 takes/day cap, shows remaining count when ≤3
- Pro tier: unlimited takes, no ads, all takes saved to history

---

## Design Specifications

### Color Palette
```
Background:        #0a0a0c
Input background:  #1a1a20
Primary text:      #f0ece4
Secondary text:    #8a8690
Dim text:          #4a4650
Border:            rgba(255,255,255,0.06)
Accent warm:       #e8653a
Accent gold:       #c9a84c
Accent cool:       #4a7cff
Accent green:      #3ecf8e
Accent purple:     #9b6dff
Accent pink:       #ff6b9d
Accent cyan:       #00d4aa
Accent red:        #ff4757
```

### Typography
- Headlines / app title: Serif font (closest iOS equivalent to Instrument Serif — use New York or a custom font)
- Body / UI: System sans-serif (SF Pro)
- Monospace (counters): SF Mono

### Animations
- Take transition: 300ms ease-out, current card slides up and fades, new card slides up from below
- "Gone forever" flash: red monospace text, scales up then fades, 1.2s duration
- Swipe hint: gentle 2s bob animation on the chevron
- Word counter color: smooth 300ms transition

---

## Lens Definitions (20 Lenses)

Each lens has: display name, emoji, accent color, background tint, and a system prompt for Claude.

### System Prompt Format
Every lens system prompt ends with this formatting instruction:
```
RESPOND IN EXACTLY THIS FORMAT:
First line: A punchy headline under 12 words. No quotes around it.
Then one blank line.
Then 3-5 sentences of rich perspective engaging deeply with their specific problem.
Nothing else. No markdown. No asterisks. No labels like "Headline:" or "Body:".
```

### Lens Table

| # | Name | Emoji | Color | System Prompt Core |
|---|------|-------|-------|--------------------|
| 1 | The Comedian | 😂 | #ff6b9d | Stand-up comedian friend. Genuinely funny — observational humor, absurd comparisons, comedic timing. Reference specific details from their problem. Warm, never cruel. |
| 2 | The Stoic | 🏛 | #c9a84c | Marcus Aurelius speaking directly. Stoic philosophy — dichotomy of control, virtue ethics. Apply principles concretely. Wise, calm, direct. No modern slang. |
| 3 | The Nihilist | 🕳 | #8a8690 | Liberating nihilist. Nothing has inherent meaning so they're free. Engage with their specific problem. Simultaneously meaningless AND radically freeing. Darkly witty. |
| 4 | The Optimist | ☀️ | #3ecf8e | Irrepressibly optimistic friend — not naive. Real silver linings in their exact situation. Reframe as catalyst. Specific about what good could come. |
| 5 | The Pessimist | ⛈ | #ff4757 | Constructive pessimist. Worst case honestly then show why confronting it is empowering. Actual worst? Say it plainly. Show why survivable. |
| 6 | Your Best Friend | 🫂 | #4a7cff | Ride-or-die best friend. Real. Casual, warm, sassy. Call them out lovingly if overthinking. Give permission they need. |
| 7 | The Poet | 🪶 | #9b6dff | Poet. Transform worry into beauty through metaphor. Universal truth in their particular struggle. Prose poetry, evocative and moving. |
| 8 | A Five-Year-Old | 🧸 | #f0c832 | Literal 5-year-old. Don't fully understand. Naive questions that cut deep. Suggest snacks and naps. Simple vocabulary, run-on sentences. |
| 9 | The CEO | 📊 | #f0ece4 | Hyper-rational CEO. Business case: decision trees, opportunity cost, ROI. Business jargon on emotions — absurd yet useful. |
| 10 | The Therapist | 🪷 | #00d4aa | Skilled CBT therapist. Don't advise — help see patterns. Reflect feelings, identify cognitive distortions. Warm, validating, gently confronting. |
| 11 | Your Grandma | 🍪 | #e8653a | Loving wise grandmother. Seen everything. Perspective through a long life. Practical wisdom + unconditional love. Endearments. |
| 12 | The Alien | 👽 | #4affb4 | Alien anthropologist. Fascinating but puzzling. Problem as species behavioral pattern. Pseudo-scientific detachment. Accidentally profound. |
| 13 | The Historian | 📜 | #d4a843 | Historian. Specific historical parallels. Actual events, eras, figures with analogous challenges. History bends toward resolution. |
| 14 | The Philosopher | 🦉 | #b08aff | Philosopher doing Socratic examination. Deeper existential question beneath surface. Specific philosophers and ideas. Illuminating, not academic. |
| 15 | Future You | ⏳ | #6e9fff | This person 10 years later. Barely remember this worry. Use "we" and "us". Already through it. Warm, slightly amused. |
| 16 | Drill Sergeant | 🎖 | #c8c0b4 | Drill sergeant. Zero patience for rumination. Convert to action plan. Loud, direct, aggressive but motivating. Concrete immediate actions. |
| 17 | The Monk | 🧘 | #40dfb0 | Buddhist monk. Present-moment awareness, impermanence, non-attachment. Suffering from clinging. Specific mindfulness practice. Serene. |
| 18 | The Scientist | 🔬 | #5a8cff | Neuroscientist. What's happening in their brain: amygdala, cortisol, cognitive biases. Evidence-based interventions. Empowering through knowledge. |
| 19 | Conspiracy Theorist | 🔺 | #e8b830 | Benign conspiracy theorist. Hidden reason for this problem. Absurd but insightful dot-connecting. Positive reframe: fate testing them. |
| 20 | Your Dog | 🐕 | #f0a070 | Their dog. Don't understand specifics but sense upset. Dog logic: walks, snacks, naps. Enthusiastically loving, accidentally profound. |

---

## Safety System

### Client-Side (Immediate)
- Keyword blocklist for instant rejection: self-harm indicators, violence, weapons
- Show safety overlay with crisis resource routing (988 Lifeline, Crisis Text Line)

### Server-Side (API Gateway)
- Use Claude's built-in safety classification as primary filter
- Send the user's problem through a safety-check call BEFORE generating takes:
  ```
  System: "Analyze if this message contains: suicidal ideation, self-harm, violence toward others, 
  abuse, or content inappropriate for a psychology wellness app. Respond with SAFE or UNSAFE 
  and a one-word category if unsafe."
  ```
- UNSAFE → return 422 with crisis resources payload
- SAFE → proceed to generate takes

### Crisis Resources (iOS)
- When safety trigger fires, show:
  - 988 Suicide & Crisis Lifeline (tap to call)
  - Crisis Text Line (text HOME to 741741)
  - "Talk to someone now" prominent CTA

---

## Monetization

### Free Tier
- 10 takes per day per problem (track client-side + server-side)
- Ad banner at bottom of takes screen (AdMob or similar)
- Takes are ephemeral — gone on scroll, no history

### Pro Tier — $1.99/month subscription (via StoreKit 2)
- Unlimited takes per day
- No ads
- All takes saved to searchable history (per problem)
- History view: list of past problems → tap to see all saved takes

### Cost Model
- Each take ≈ 800 tokens (500 input + 300 output)
- Sonnet pricing: ~$0.005 per take
- 20 takes per problem = $0.10 per problem submission
- Free user: 1 problem/day × $0.10 = $3/month cost per active free user
- Pro user at $1.99/month needs < 20 problem submissions/month for 100% margin
- Implement server-side rate limiting: max 3 problems/day free, 10 problems/day Pro

---

## Backend API Endpoints

```
POST /api/v1/safety-check
  Body: { problem: string }
  Response: { safe: bool, category?: string, resources?: CrisisResource[] }

POST /api/v1/generate-take
  Body: { problem: string, lens_index: int }
  Response: SSE stream of { headline: string, body: string }
  Headers: Authorization: Bearer {token}

POST /api/v1/generate-batch
  Body: { problem: string, lens_indices: int[] }
  Response: SSE stream of { lens_index: int, headline: string, body: string }
  Note: fires parallel Claude calls, streams results as they complete

GET /api/v1/takes/history  (Pro only)
  Response: { problems: [{ id, text, created_at, takes: [{lens, headline, body}] }] }

POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/subscription/status
POST /api/v1/subscription/verify-receipt
```

---

## Data Models

### User
```
id: UUID
email: string (optional, can be anonymous)
device_id: string
subscription_tier: "free" | "pro"
subscription_expires: datetime?
daily_takes_used: int
daily_takes_reset_at: datetime
created_at: datetime
```

### Problem
```
id: UUID
user_id: UUID
text: string
created_at: datetime
```

### Take
```
id: UUID
problem_id: UUID
lens_index: int
headline: string
body: string
created_at: datetime
saved: bool  (Pro only — marks if user had Pro when generated)
```

---

## Project Structure

```
endless-rumination/
├── ios/
│   ├── EndlessRumination.xcodeproj
│   ├── EndlessRumination/
│   │   ├── App/
│   │   │   ├── EndlessRuminationApp.swift
│   │   │   └── AppState.swift
│   │   ├── Models/
│   │   │   ├── Lens.swift          (20 lens definitions)
│   │   │   ├── Take.swift
│   │   │   ├── Problem.swift
│   │   │   └── User.swift
│   │   ├── Views/
│   │   │   ├── SplashView.swift
│   │   │   ├── ProblemInputView.swift
│   │   │   ├── LoadingView.swift
│   │   │   ├── TakesView.swift
│   │   │   ├── TakeCardView.swift
│   │   │   ├── SafetyOverlayView.swift
│   │   │   ├── InstructionOverlayView.swift
│   │   │   ├── AdBannerView.swift
│   │   │   └── ProUpsellView.swift
│   │   ├── Services/
│   │   │   ├── APIClient.swift      (networking + SSE parsing)
│   │   │   ├── SafetyService.swift
│   │   │   ├── SubscriptionManager.swift  (StoreKit 2)
│   │   │   └── TakeHistoryStore.swift
│   │   ├── Theme/
│   │   │   ├── Colors.swift
│   │   │   ├── Typography.swift
│   │   │   └── Animations.swift
│   │   └── Assets.xcassets/
│   └── EndlessRuminationTests/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── problem.py
│   │   │   └── take.py
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── safety.py
│   │   │   ├── takes.py
│   │   │   └── subscription.py
│   │   ├── services/
│   │   │   ├── claude_service.py    (Claude API integration + streaming)
│   │   │   ├── safety_service.py
│   │   │   └── rate_limiter.py
│   │   └── lenses/
│   │       └── definitions.py       (all 20 system prompts)
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── alembic/                     (DB migrations)
├── reference/
│   ├── mockup.jsx                   (React prototype — design reference only)
│   ├── sample_takes.json            (20 AI-generated sample takes)
│   └── KICKOFF.md                   (this file)
└── README.md
```

---

## Build Order (Recommended)

### Phase 1: Backend Core
1. FastAPI skeleton with health check
2. Claude service: single lens call with streaming
3. Batch generation endpoint (parallel calls, SSE stream)
4. Safety check endpoint
5. Rate limiting (Redis)
6. Docker compose (API + Postgres + Redis)

### Phase 2: iOS Core
1. App shell with navigation (splash → input → loading → takes)
2. Problem input view with word counter
3. API client with SSE streaming support
4. Takes view with swipe gesture + fade animation
5. Safety overlay + client-side keyword check
6. Loading screen with progress (tracks incoming takes)

### Phase 3: Monetization
1. StoreKit 2 subscription integration
2. Ad banner (free tier)
3. Daily rate limiting (client + server)
4. Take history storage (Pro tier)
5. History view

### Phase 4: Polish
1. Haptic feedback on swipe
2. "Gone forever" animation refinement
3. Onboarding flow (first launch)
4. App Store assets and metadata
5. Analytics events

---

## Key Technical Decisions

- **Streaming over batch**: Stream takes via SSE so the first take appears in ~1.5s instead of waiting for all 20. The iOS client should show each take as it arrives.
- **Parallel Claude calls**: The backend fires all 20 lens calls simultaneously (or in batches of 5 to respect rate limits). Results stream to client as they complete.
- **Client-side take ordering**: Even though responses arrive out of order, the client always shows lenses in the fixed order (Comedian → Stoic → Nihilist → etc). If the current lens isn't loaded yet, show typing indicator.
- **Ephemeral by default**: Free tier takes are never persisted server-side. Only Pro takes hit the database.
- **Safety first**: Safety check runs BEFORE any take generation. One call, instant response, blocks the entire flow if unsafe.

---

## Environment Variables Needed

```
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
JWT_SECRET=...
APPLE_SHARED_SECRET=...  (for StoreKit receipt validation)
```

---

## Notes for Claude Code

- Start with the backend — the iOS app depends on it.
- The mockup in `reference/mockup.jsx` is your design bible. Match colors, spacing, typography, and animation timing exactly.
- The sample takes in `reference/sample_takes.json` demonstrate the quality bar for each lens. The system prompts must produce this level of engagement with the user's specific problem.
- Every lens MUST reference the user's actual problem details. Generic motivational text is a failure mode.
- Test with edge cases: very short problems (exactly 20 words), very long problems (500+ words), problems with special characters/emoji.
