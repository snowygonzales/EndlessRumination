# CLAUDE.md — Endless Rumination

## Project Overview
Psychology app with two independent native frontends (SwiftUI iOS + Jetpack Compose Android) + Python backend (FastAPI). Users describe a problem, then doom-scroll through AI-generated perspectives from different personas. Each perspective fades forever unless user is a Pro subscriber. Base lenses (0-19) come with free/Pro tiers; purchasable Voice Packs (20-39) add 5 historical-figure voices each.

**Architecture:** Two fully native apps sharing code by convention (same API contract, models, design system, business rules) — not by shared code. The backend is platform-agnostic. KMP (Compose Multiplatform) was previously used but abandoned due to rendering quality issues on iOS; `multiplatform/` is archived as reference only.

### On-Device Inference Experiment (Active)
**Branch:** `experiment/on-device-inference` (cloud API preserved on `master`, tagged `v0.4.0-cloud-api`)
**Full guide:** `experiment_steps.md` — **read this FIRST** for any experiment-related work.

Pivoting from cloud Claude API to fully on-device inference using fine-tuned **Qwen 3.5 4B** via **Apple MLX**. Goal: privacy-first iOS app positioned for App Store featuring ("your thoughts never leave this device").

**Status:** Steps 1-6 complete (dataset, MLX verify, SFT, DPO, merge, eval, optimize, MLX convert, iOS refactor). Build 19 fixes tokenizer crash. Build 20 adds safety hardening, UX fixes, Pro take navigation. **Next: Step 7 — device testing.**

Key tech choices:
- **Model:** Qwen 3.5 4B only (2B dropped — insufficient comprehension) — Gated DeltaNet architecture
- **Training:** Unsloth with **bf16 LoRA** (NOT QLoRA — breaks Gated DeltaNet)
- **Inference:** Apple MLX via mlx-swift (~40% faster than llama.cpp, WWDC 2025 featured)
- **iOS minimum:** iOS 18 (up from 17, required by mlx-swift Metal kernels)
- **Optimized model:** Vision encoder stripped + vocab pruned (248K→140K tokens), 4-bit ≈ 2.0 GB, targets 6GB devices
- **Generation params:** temperature=0.7, top_k=40, top_p=0.95
- **Budget:** $93.55 of $100 spent on dataset generation (Sonnet + Haiku API calls)

## Key Commands
- Backend (local): `cd backend && source .venv/bin/activate && uvicorn app.main:app --reload`
- Backend (Docker): `cd backend && docker-compose up`
- Backend tests: `cd backend && pytest -v` (42 tests, all passing — SQLite + mocked Claude)
- iOS project: `cd ios && xcodegen generate && open EndlessRumination.xcodeproj`
- iOS tests: Cmd+U in Xcode (9 tests)
- iOS debug build (generic): `cd ios && xcodegen generate && xcodebuild -scheme EndlessRumination -sdk iphoneos -destination generic/platform=iOS -configuration Debug -derivedDataPath /tmp/ER-Debug build`
- iOS install on device: `xcrun devicectl device install app --device "9C36724C-82EF-534E-8B33-A51283B7EE70" /tmp/ER-Debug/Build/Products/Debug-iphoneos/EndlessRumination.app` (device must be unlocked)
- iOS stream device logs: `log stream --predicate 'subsystem == "com.endlessrumination"' --style compact`
- **Connected device**: iPhone 14 (iPhone14,7), CoreDevice ID: `9C36724C-82EF-534E-8B33-A51283B7EE70`, xcodebuild ID: `00008110-001C50110E88201E`
- iOS TestFlight: `cd ios && xcodegen generate && xcodebuild -scheme EndlessRumination -sdk iphoneos -configuration Release -archivePath /tmp/ER-iOS.xcarchive archive && xcodebuild -exportArchive -archivePath /tmp/ER-iOS.xcarchive -exportOptionsPlist /tmp/ExportOptions.plist -exportPath /tmp/ER-iOS-Export -allowProvisioningUpdates -authenticationKeyPath ~/.appstoreconnect/private_keys/AuthKey_8YM9M9P47X.p8 -authenticationKeyID 8YM9M9P47X -authenticationKeyIssuerID e5829743-777b-4a9f-a968-30a8714fb272`
- Android build: `cd android && JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew :app:assembleDebug`
- Android install: `~/Library/Android/sdk/platform-tools/adb install -r android/app/build/outputs/apk/debug/app-debug.apk`
- Android release: `cd android && JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew :app:bundleRelease`
- Android publish to Play Internal Testing: `cd android && JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home ./gradlew :app:publishReleaseBundle` (requires `play-service-account.json`)
- Android emulator: `~/Library/Android/sdk/emulator/emulator -avd Pixel_API_35 &`
- Deploy to Railway: `railway up --detach` (from project root)

### On-Device Experiment Commands (Mac)
- Distillation scripts: `source backend/.venv/bin/activate && python scripts/distillation/<script>.py`
- MLX inference test: `source .mlx-venv/bin/activate && python -m mlx_lm.generate --model mlx-community/Qwen3.5-4B-4bit --prompt "test"`
- Budget check: `source backend/.venv/bin/activate && python -c "from scripts.distillation.cost_tracker import print_budget_status; print_budget_status()"`

### On-Device Experiment Commands (PC/WSL2)
- Activate venv: `source ~/er-train-venv/bin/activate && cd ~/er-training`
- SFT 4B (verified): `python scripts/training/sft_train.py --model 4b --batch-size 4 --grad-accum 4`
- DPO training: `python scripts/training/dpo_train.py --model 4b`
- Merge LoRA + export: `python scripts/training/merge_and_export.py --model 4b`
- Optimize for device: `python scripts/training/optimize_for_device.py --model 4b --prune-vocab`
- MLX convert (Mac): `python -m mlx_lm.convert --model ./models/er-qwen35-4b-optimized --quantize --q-bits 4 --q-group-size 64 -o ./models/er-qwen35-4b-mlx-4bit`
- Eval UI: `pip install gradio && python scripts/evaluation/eval_ui.py --model-path models/er-qwen35-4b-dpo --adapter` (accessible at `http://<PC_IP>:7860`)
- ⚠️ MUST run from native Linux FS (`~/er-training/`), NOT `/mnt/c/` — severe I/O bottleneck otherwise

## Architecture
- Two native frontends → FastAPI gateway → Claude Sonnet/Haiku hybrid API
- Free tier: 5 random lenses from all 20 each run, forward-only (takes gone forever)
- Pro ($9.99/mo): All 20 base lenses, bidirectional take navigation within a session, no ads
- Voice Packs ($4.99 each, non-consumable IAP): 4 packs × 5 voices (indices 20-39), all Sonnet
  - Strategists (20-24), Revolutionaries (25-29), Philosophers (30-34), Creators (35-39)
  - Pack voices append after base takes in the doom scroll
- PostgreSQL for users/takes, Redis for rate limiting (optional, degrades gracefully)
- SSE streaming for real-time take delivery
- xcodegen for iOS Xcode project generation (project.yml → .xcodeproj)
- **Safety layers (on-device):** Input blocklist with Unicode normalization + safety preamble in all system prompts + output blocklist on model responses + functional report/flag button with crisis resources

## Directory Structure
```
EndlessRumination/
├── backend/                    # FastAPI backend (Python)
├── ios/                        # SwiftUI native iOS app
├── android/                    # Jetpack Compose native Android app
├── scripts/
│   ├── create_asc_products.py  # IAP product creation (App Store Connect)
│   ├── create_play_products.py # IAP product creation (Google Play)
│   ├── distillation/           # Dataset generation pipeline (Mac, steps 1.1-1.6)
│   ├── training/               # Fine-tuning scripts (PC/WSL2, steps 3-4)
│   └── evaluation/             # Gradio eval UI (PC/WSL2, step 4.4)
├── data/                       # Generated training data (gitignored)
├── models/                     # Trained models + MLX exports (gitignored)
├── .mlx-venv/                  # Python 3.12 venv for MLX (gitignored)
├── multiplatform/              # ARCHIVED — KMP reference code only
├── docs/                       # Privacy policy, ToS, support, release checklist
├── experiment_steps.md         # On-device inference pipeline guide
├── CLAUDE.md
└── KICKOFF.md
```

## Environment & Infrastructure

### Mac Mini M1 (dataset generation, iOS builds, model conversion)
- **Machine**: Mac Mini M1, macOS, Xcode 16, Python 3.9 (system)
- **Python 3.12** via Homebrew for MLX: `/opt/homebrew/opt/python@3.12/bin/python3.12`, venv at `.mlx-venv/`
- **JDK**: OpenJDK 17 via Homebrew (`JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home`)
- **Android SDK**: `~/Library/Android/sdk` (cmdline-tools, platform-tools, emulator, API 35 ARM64)
- **iOS simulator**: iPhone 17 Pro (ID: `8C545099-AF9E-4D62-A716-E0826851F18D`)
- PostgreSQL 16 + Redis via Homebrew (not Docker)

### PC with RTX 5090 (training only, via WSL2)
- **GPU**: NVIDIA RTX 5090 (32GB VRAM), Blackwell architecture (SM_120)
- **Runtime**: WSL2 (not native Windows)
- **PyTorch**: Must use nightly with CUDA 12.8 (`pip install torch --extra-index-url https://download.pytorch.org/whl/cu128`)
- Flash Attention 2/3 do NOT work on Blackwell — Unsloth uses Triton kernels instead
- WSL2 has phantom OOM errors — start conservative, scale up

### Cloud Infrastructure
- **Production API**: https://backend-production-5537.up.railway.app
- **Railway dashboard**: https://railway.com/project/30951286-357e-4529-a21c-bb527d62eb13
- **Privacy policy**: https://github.com/snowygonzales/EndlessRumination/blob/master/docs/privacy-policy.md
- **Terms of Service**: https://github.com/snowygonzales/EndlessRumination/blob/master/docs/terms-of-service.md
- **Support page**: https://github.com/snowygonzales/EndlessRumination/blob/master/docs/support.md
- **Release checklist**: `docs/release_todo.md` — manual console tasks remaining before launch
- **GitHub repo**: Public (required for reviewer-accessible privacy policy/ToS URLs)
- iOS debug builds → localhost:8000, release builds → Railway URL
- Android always uses Railway production URL

### CLI Publishing (both platforms — no GUI needed)
- **iOS → TestFlight**: App Store Connect API key `8YM9M9P47X` at `~/.appstoreconnect/private_keys/AuthKey_8YM9M9P47X.p8`, Issuer `e5829743-777b-4a9f-a968-30a8714fb272`. Bundle ID: `com.endlessrumination.EndlessRumination`. ExportOptions plist at `/tmp/ExportOptions.plist` (method: app-store-connect, teamID: R6N5B4SDWH, destination: upload, signingStyle: automatic).
- **Android → Google Play Internal Testing**: Google Cloud service account (`play-service-account.json` in `android/`, gitignored) linked via Google Play Console Users & Permissions — `./gradlew :app:publishReleaseBundle` builds signed AAB + uploads to internal track
- **Google Play Console**: Account ID `6253718630117210435`, app package `com.endlessrumination`, developer identity verified
- **Google Cloud project**: `endless-rumination` — Android Publisher API enabled, service account created and linked to Play Console

## Important Files

### iOS (SwiftUI)
- `ios/project.yml` — xcodegen project definition (SPM packages, build settings, Info.plist)
- `ios/EndlessRumination/App/EndlessRuminationApp.swift` — App entry point, GAD init, ATT prompt, AI consent overlay
- `ios/EndlessRumination/App/AppState.swift` — @Observable state management, AI consent persistence
- `ios/EndlessRumination/Services/InferenceEngine.swift` — On-device MLX LLM inference (model download, loading, generation)
- `ios/EndlessRumination/Services/LocalTakeGenerator.swift` — Sequential per-lens take generation using InferenceEngine
- `ios/EndlessRumination/Services/DeviceCapability.swift` — RAM/memory checks for model compatibility
- `ios/EndlessRumination/Services/SubscriptionManager.swift` — StoreKit 2 billing, receipt verification
- `ios/EndlessRumination/Services/SafetyService.swift` — Client blocklist safety check
- `ios/EndlessRumination/Models/` — Take, Lens, VoicePack, LensPrompts
- `ios/EndlessRumination/Views/` — All screens + AdBannerView, AIConsentView, OnboardingView
- `ios/EndlessRumination/Theme/` — ERColors, ERTypography, ERAnimations

### Android (Jetpack Compose)
- `android/app/build.gradle.kts` — App build config (Compose BOM, Ktor, billing, ads, signing)
- `android/app/src/main/kotlin/.../MainActivity.kt` — Activity entry point, MobileAds + HapticService init
- `android/app/src/main/kotlin/.../App.kt` — Root composable, AnimatedContent navigation, billing lifecycle, AI consent overlay
- `android/app/src/main/kotlin/.../AppState.kt` — ViewModel state management (mutableStateOf, BillingCallback, receipt verification)
- `android/app/src/main/kotlin/.../ApiClient.kt` — Ktor HTTP + SSE streaming, auth + receipt endpoints
- `android/app/src/main/kotlin/.../Platform.kt` — BASE_URL constant
- `android/app/src/main/kotlin/.../service/BillingService.kt` — Google Play Billing v7
- `android/app/src/main/kotlin/.../service/BillingModels.kt` — Billing types, sealed classes, product IDs
- `android/app/src/main/kotlin/.../service/HapticService.kt` — Vibration feedback
- `android/app/src/main/kotlin/.../service/SafetyService.kt` — Client blocklist + server safety check
- `android/app/src/main/kotlin/.../service/ActivityProvider.kt` — Activity context for billing
- `android/app/src/main/kotlin/.../model/` — Take, Lens (with isFree/isWise), VoicePack, User, AuthResponse
- `android/app/src/main/kotlin/.../ui/` — All screens + PlatformAdBanner, AIConsentScreen, OnboardingScreen
- `android/app/src/main/kotlin/.../theme/` — ERColors, ERTypography

### Backend
- `KICKOFF.md` — Complete project spec, read this FIRST
- `reference/mockup.jsx` — React prototype with exact design specs (DO NOT build React, extract design only)
- `reference/sample_takes.json` — Quality bar for AI-generated takes
- `backend/app/lenses/definitions.py` — Base 20 lens system prompts (indices 0-19)
- `backend/app/lenses/voice_packs.py` — Voice pack definitions (indices 20-39, 4 packs × 5 voices)
- `backend/app/services/receipt_validator.py` — Abstract receipt validation base
- `backend/app/services/apple_validator.py` — App Store Server API v2 validation
- `backend/app/services/google_validator.py` — Google Play Developer API validation
- `railway.toml` — Railway deployment config

### Scripts
- `scripts/create_asc_products.py` — Creates/updates all IAP products in App Store Connect via REST API (JWT auth, idempotent)
- `scripts/create_play_products.py` — Creates subscription in Google Play via API (voice packs require Play Console UI)

### Distillation Scripts (on-device experiment, Mac)
- `scripts/distillation/cost_tracker.py` — Shared $100 pipeline budget tracker (`data/.pipeline_cost_tracker.json`)
- `scripts/distillation/generate_seeds.py` — Step 1.1: 200 seed worry prompts via Sonnet
- `scripts/distillation/expand_seeds.py` — Step 1.2: Expand to 1,197 prompts + dedup
- `scripts/distillation/generate_responses.py` — Step 1.3: 14,520 teacher responses via Sonnet (20 lenses × prompts)
- `scripts/distillation/filter_quality.py` — Step 1.4: Haiku scoring, 4+ on all dimensions → 8,850 kept (61%)
- `scripts/distillation/generate_dpo_pairs.py` — Step 1.5: 1,900 intentionally bad response pairs
- `scripts/distillation/format_training_data.py` — Step 1.6: ChatML format + 90/10 train/val split

### Training Scripts (on-device experiment, PC/WSL2)
- `scripts/training/sft_train.py` — Steps 3.2-3.3: bf16 LoRA SFT via Unsloth
- `scripts/training/dpo_train.py` — Steps 4.1-4.2: DPO alignment (vanilla PEFT + TRL, NOT Unsloth)
- `scripts/training/merge_and_export.py` — Step 4.3: Merge LoRA + export to HF format
- `scripts/training/optimize_for_device.py` — Step 4.5: Strip vision encoder + prune vocab for 6GB devices

### Evaluation Scripts (on-device experiment, PC or Mac)
- `scripts/evaluation/eval_ui.py` — Step 4.4: Gradio web UI for human quality evaluation (all 40 lenses, batch mode, ratings)

### Archived
- `multiplatform/` — KMP Compose Multiplatform code (archived, reference only)

## Conventions
- Swift: SwiftUI only, iOS 17+, @Observable (not Combine), no UIKit unless necessary, no third-party UI deps
- Kotlin: Jetpack Compose, ViewModel for state, Ktor for networking, Material Icons (not SF Symbols)
- Python: FastAPI, async everywhere, type hints, Pydantic models, `from __future__ import annotations` (Python 3.9 compat)
- All lens system prompts end with the standard format instruction (see KICKOFF.md)
- Color values defined in KICKOFF.md are authoritative — match exactly
- API cost: ~$0.01/free submission (1 Sonnet + 4 Haiku), ~$0.12/Pro submission (20 Sonnet), ~$0.025 per pack (5 Sonnet)
- Backend config `free_sonnet_lens_indices: [1, 9]` marks which lenses use Sonnet for free users — but free users only access indices 0-4, so only index 1 is effectively Sonnet
- "Wise" badge on Sonnet takes (including all pack voices), "Quick take · Powered by Haiku" on Haiku takes
- Triple-tap Shop button in DEBUG builds to toggle Pro status (simulator cheat)
- Voice pack indices 20-39 extend the base lens system; `Lens.displayInfo(index)` provides unified lookup (Kotlin), `Lens.displayInfo(at:)` (Swift)
- State-based nav: `AppScreen` enum + `when` (Kotlin) / `switch` (Swift)

## Android Distribution (Google Play Internal Testing)
Google Play Internal Testing is the Android equivalent of TestFlight. Uses `gradle-play-publisher` plugin for CLI uploads. **Full CLI pipeline verified and working.**

**Setup (all complete):**
1. Release keystore at `android/release.keystore` (gitignored), credentials in `android/keystore.properties` (gitignored)
2. `gradle-play-publisher` plugin (`com.github.triplet.play:3.11.0`) configured in `app/build.gradle.kts`
3. Play Console: app `com.endlessrumination` created, Internal Testing track set up with initial AAB upload
4. Google Cloud: `endless-rumination` project, Android Publisher API enabled, service account created
5. Service account linked to Play Console via Users & Permissions (not Setup → API access, which no longer exists)
6. Service account JSON key at `android/play-service-account.json` (gitignored)

**CLI publish flow:**
- `cd android && JAVA_HOME=... ./gradlew :app:publishReleaseBundle` — builds signed AAB + uploads to internal testing
- Developer identity now verified. Currently `ReleaseStatus.DRAFT` — change to `ReleaseStatus.COMPLETED` in `app/build.gradle.kts` for auto-rollout to testers
- Testers get notified in Play Store → install/update via normal Play Store flow
- No "Install from unknown sources" needed, auto-updates work
- Remember to bump `versionCode` in `app/build.gradle.kts` before each publish (currently at 6)

## Monetization (IAP + Ads + Backend Validation)

### IAP Product Setup (App Store Connect)
All 5 iOS IAP products are created and priced in App Store Connect via `scripts/create_asc_products.py`:

| Product ID | Type | Price | ASC ID |
|-----------|------|-------|--------|
| `com.endlessrumination.pro.monthly` | Auto-renewable subscription | $9.99/mo | 6759655515 |
| `com.endlessrumination.pack.strategists` | Non-consumable | $4.99 | 6759794696 |
| `com.endlessrumination.pack.revolutionaries` | Non-consumable | $4.99 | 6759794840 |
| `com.endlessrumination.pack.philosophers` | Non-consumable | $4.99 | 6759794841 |
| `com.endlessrumination.pack.creators` | Non-consumable | $4.99 | 6759794982 |

- Subscription group: "Endless Rumination Pro" (ID: 21952994)
- All products have en-US localizations and USD pricing set
- Script is idempotent (handles 409 conflicts, looks up existing products)
- **To re-run**: `source backend/.venv/bin/activate && python3 scripts/create_asc_products.py` (requires PyJWT, cryptography, requests)
- **Remaining steps**: Upload review screenshots for each product, then submit with next app version

### IAP Product Setup (Google Play)
All 5 Android IAP products are created in Google Play Console:

| Product ID | Type | Price |
|-----------|------|-------|
| `com.endlessrumination.pro.monthly` | Subscription (P1M) | $9.99/mo |
| `com.endlessrumination.pack.strategists` | One-time (managed) | $4.99 |
| `com.endlessrumination.pack.revolutionaries` | One-time (managed) | $4.99 |
| `com.endlessrumination.pack.philosophers` | One-time (managed) | $4.99 |
| `com.endlessrumination.pack.creators` | One-time (managed) | $4.99 |

- Subscription created via API (`scripts/create_play_products.py`), base plan `monthly-autorenew` (ACTIVE)
- Voice packs created via Play Console UI (legacy `inappproducts` API blocked — "Please migrate"; modern `onetimeProducts` endpoint returns 404)
- **To re-run subscription only**: `source backend/.venv/bin/activate && python3 scripts/create_play_products.py`
- Products testable immediately by internal testers

### iOS Billing (StoreKit 2)
- `SubscriptionManager` — @Observable, uses StoreKit 2 async APIs directly
- `Transaction.currentEntitlements` on launch (no Apple ID prompt)
- `verifyReceiptOnServer()` called after each purchase (background, non-blocking)
- Restore purchases button in ShopView

### Android Billing (Google Play Billing v7)
- `BillingService` — standalone class wrapping `BillingClient`, calls `onReceiptReady` after purchase
- `AppState : ViewModel(), BillingCallback` — receives purchase state changes, verifies receipts on server via `viewModelScope`
- `App.kt` lifecycle: `LaunchedEffect` → `initialize()` + `loadProducts()` + `checkEntitlements()`; `DisposableEffect` → `dispose()`
- Product IDs: `com.endlessrumination.pro.monthly` (subscription), `com.endlessrumination.pack.{strategists,revolutionaries,philosophers,creators}` (one-time)
- Purchase error messages displayed on ProUpgrade + PackDetail screens; loading spinner on both

### AdMob (real IDs on both platforms)
- **iOS**: `BannerAdRepresentable` (UIViewRepresentable wrapping GADBannerView), ad unit `ca-app-pub-5300605522420042/1359255336`, debug uses test ID `ca-app-pub-3940256099942544/2435281174`
- **Android**: `PlatformAdBanner` (AndroidView wrapping AdView), ad unit `ca-app-pub-5300605522420042/6942754502`
- **iOS SDK**: Google Mobile Ads 11.13.0 via SPM
- **Android SDK**: play-services-ads 23.6.0
- **AndroidManifest.xml**: AdMob app ID `ca-app-pub-5300605522420042~5657592998`
- **iOS Info.plist**: `GADApplicationIdentifier` = `ca-app-pub-5300605522420042~6341428784`, plus SKAdNetwork IDs
- Banner shown on TakesScreen when `!isPro`, 50dp height

### Backend Receipt Validation
- **`POST /api/v1/subscription/verify-receipt`** — routes to Apple or Google validator by `platform` field
- **Apple**: App Store Server API v2 with JWT auth (.p8 key) → GET signed transaction → decode JWS → extract productId/expiry
- **Google**: Google Play Developer API with service account → `subscriptionsv2.get` / `products.get`
- Config: `apple_key_id`, `apple_issuer_id`, `apple_private_key_path`, `google_play_service_account_json` in Settings
- Updates user `subscription_tier` (pro) or `owned_pack_ids` (comma-separated) in DB
- Both clients call verify receipt after each successful purchase (background, non-blocking)
- 7 backend tests in `test_subscription.py` (mocked validators)

### Current Build Numbers
- iOS: v1.0.0 build 20 (on-device inference, safety hardening, UX fixes)
- Android: versionCode 6 (Internal Testing, DRAFT status — still cloud API)

## Tech Stacks

### iOS
- SwiftUI, iOS 17+, @Observable
- URLSession for HTTP + SSE (async/await)
- StoreKit 2 for IAP
- Google Mobile Ads 11.13.0 via SPM
- xcodegen for project generation

### Android
- Jetpack Compose (BOM 2024.12.01), Material3
- Ktor 3.1.1 (OkHttp engine) for HTTP + SSE
- Kotlinx.serialization 1.8.0, Kotlinx.coroutines 1.10.1
- Google Play Billing v7 (billing-ktx 7.1.1)
- play-services-ads 23.6.0
- Kotlin 2.1.20, AGP 8.7.3, Gradle 8.11.1
- min SDK 26, target SDK 35
- Requires JAVA_HOME pointing to OpenJDK 17

## Launch Compliance (both platforms)
All code-level app store compliance items are implemented:
- **AI consent dialog** — Names Anthropic/Claude, gates first problem submission (UserDefaults/SharedPreferences)
- **Content report/flag** — Flag icon on take cards with confirmation dialog
- **Medical disclaimer** — "Not a substitute for professional mental health care" on input + shop screens
- **ATT prompt** — iOS: `ATTrackingManager.requestTrackingAuthorization` on app become active
- **AD_ID permission** — Android: `com.google.android.gms.permission.AD_ID` in manifest
- **Subscription terms** — Full auto-renewal/cancellation disclosure on paywall + Privacy Policy/ToS links
- **Account deletion** — In-app delete option in Shop → opens mailto: flow
- **Privacy Policy** — Accurate AdMob, AI processing, GDPR/CCPA disclosures (`docs/privacy-policy.md`)
- **Terms of Service** — AI content disclaimer, subscription terms, liability limits (`docs/terms-of-service.md`)
- **Remaining manual tasks** — See `docs/release_todo.md`

## Deployment Rules
- **NEVER push to TestFlight or App Store without explicit user command** — always ask and wait for confirmation before archiving/uploading
- **NEVER push to Google Play without explicit user command** — same rule applies
- Default to debug builds directly to connected device for testing
- Use `os.log` with `Logger(subsystem: "com.endlessrumination", category: "<ClassName>")` for all debug logging
- Stream device logs with: `log stream --predicate 'subsystem == "com.endlessrumination"' --style compact`

## What NOT to Do
- Don't build a React/web app
- Don't push to TestFlight / App Store / Google Play without explicit user permission
- Don't use UIKit storyboards
- Don't use KMP/Compose Multiplatform (archived, use native only)
- Don't hardcode API keys — use environment variables
- Don't persist free-tier takes to database
- Don't skip the safety check before generating takes
- Don't commit .xcodeproj — it's generated by xcodegen and gitignored
- Don't commit .venv, .mlx-venv, .env, data/, or models/
- Don't use QLoRA (4-bit) for Qwen 3.5 — bf16 LoRA only (Gated DeltaNet architecture is sensitive to quantization during training)
- Don't install mlx-lm from PyPI (v0.29.1 lacks Qwen 3.5 support) — install from git
- Don't use `temp=` kwarg with mlx-lm 0.30+ generate — use `sampler=make_sampler(temp=0.7)` from `mlx_lm.sample_utils`
- Don't forget `enable_thinking=False` for Qwen 3.5 4B — otherwise it wastes ~100 tokens on chain-of-thought
- Don't use Unsloth's DPOTrainer with Qwen 3.5 — it misidentifies qwen3_5 as a vision model and crashes with `KeyError: 'images'`. Use vanilla transformers + PEFT + TRL instead (see `dpo_train.py` and `experiment_steps.md` step 4)
- Don't use non-ASCII characters (em dashes, curly quotes, accented names) in LensPrompts.swift — the pruned vocab is missing 128 high-byte characters (0x80-0xFF), causing swift-transformers to crash with `Fatal error: Unexpectedly found nil while unwrapping an Optional value` at `Tokenizer.swift:643`. Use `--` instead of `—`, `Soren` instead of `Søren`, etc.
- Don't forget the vocab pruning limitation: the optimized model's BPE tokenizer cannot encode non-ASCII characters. User input should be sanitized to ASCII before tokenization. Future fix: re-run `optimize_for_device.py` with byte tokens forced to keep.
