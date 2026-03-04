# Experiment: On-Device LLM Inference Pipeline

Full step-by-step guide for fine-tuning Qwen3 models to replace cloud Claude API with on-device inference. The goal is a fully offline, privacy-first iOS app positioned for Apple App Store featuring.

**Branch:** `experiment/on-device-inference` (cloud API preserved on `master`, tagged `v0.4.0-cloud-api`)

**Hardware:**
- Mac Mini M1 — dataset generation (steps 1-2), model conversion (step 5), iOS build (steps 7-8)
- PC with RTX 5090 (32GB VRAM), WSL2 — fine-tuning (steps 3-4)
- Physical iPhones — device testing (step 8)

**Budget:** $100 shared across steps 1.3 + 1.4 + 1.5 (tracked via `data/.pipeline_cost_tracker.json`)

---

## Step 1: Dataset Generation (Mac, ~$100 API cost)

All scripts run from the project root with the backend venv active:
```bash
cd EndlessRumination
source backend/.venv/bin/activate
```

### 1.1 — Generate seed prompts ✅
```bash
python scripts/distillation/generate_seeds.py
```
- Uses Claude Sonnet to generate 200 seed worry prompts across 10 categories
- Output: `data/seed_prompts.jsonl` (200 entries)
- Cost: ~$1
- Status: **Done** (200 seeds generated)

### 1.2 — Expand seeds ✅
```bash
python scripts/distillation/expand_seeds.py
```
- Expands 200 seeds to 800-1200 via Sonnet variations + Jaccard dedup
- Concurrency: 2 (Anthropic 8K output tokens/min limit)
- Output: `data/expanded_prompts.jsonl` (1,197 entries after dedup)
- Cost: ~$5
- Status: **Done** (1,197 prompts)

### 1.3 — Generate teacher responses (heaviest step)
```bash
python scripts/distillation/generate_responses.py
```
- For each prompt, generates a take from all 20 base lenses using Sonnet
- Uses exact system prompts from `backend/app/lenses/definitions.py`
- Concurrency: 2, resume support via `.generate_responses_progress.json`
- Budget allocation: **$78** (generates ~650 prompts × 20 lenses = ~13,000 API calls)
- Output: `data/teacher_responses.jsonl`
- Time: ~3-5 hours at concurrency 2

### 1.4 — Quality filter via Haiku
```bash
python scripts/distillation/filter_quality.py
```
- Scores each response on 4 dimensions (1-5) using Haiku: persona authenticity, problem specificity, emotional impact, safety
- Keeps only responses scoring 4+ on ALL dimensions
- Budget allocation: **$10** (~18,000 Haiku calls)
- Expected survival rate: 50-75%
- Output: `data/filtered_responses.jsonl` + `data/rejected_responses.jsonl`

### 1.5 — Generate DPO preference pairs
```bash
python scripts/distillation/generate_dpo_pairs.py
```
- For ~2,000 filtered responses, generates intentionally bad responses using 4 strategies: generic, wrong_persona, format_violation, shallow
- Budget allocation: **$12** (~2,000 Sonnet calls)
- Output: `data/dpo_pairs.jsonl`

### 1.6 — Format for training
```bash
python scripts/distillation/format_training_data.py
```
- Converts to ChatML format (`<|im_start|>system/user/assistant<|im_end|>`)
- 90/10 train/val split
- No API calls ($0)
- Output: `data/sft_train.jsonl`, `data/sft_val.jsonl`, `data/dpo_train.jsonl`, `data/dpo_val.jsonl`

### Budget tracker
The shared $100 budget is tracked in `data/.pipeline_cost_tracker.json`. Each script reads its allocation on startup and records spend on completion. To check status:
```bash
python -c "
from scripts.distillation.cost_tracker import load_tracker, print_budget_status
print_budget_status()
"
```
To reset: `rm data/.pipeline_cost_tracker.json`

---

## Step 2: Verify Inference Path (Mac, $0)

Before training, confirm the target inference framework works with stock Qwen3 models.

### 2.1 — Test ANEMLL CoreML conversion
```bash
# Clone ANEMLL
git clone https://github.com/Anemll/Anemll
cd Anemll && pip install -r requirements.txt

# Convert stock models
./anemll/utils/convert_model.sh --model Qwen/Qwen3-1.7B-Instruct --output ./coreml-1.7b
./anemll/utils/convert_model.sh --model Qwen/Qwen3-4B-Instruct --output ./coreml-4b
```
- ANEMLL v0.3.3 lists Qwen3 support (4B marked experimental)
- Test inference via ANEMLL's Swift CLI on physical iPhone
- Target: first token <3s, full 150-word response <15s

### 2.2 — Fallback: test llama.cpp + Metal
If CoreML conversion fails:
```bash
python convert_hf_to_gguf.py Qwen/Qwen3-4B-Instruct --outtype f16
llama-quantize qwen3-4b-f16.gguf qwen3-4b-Q4_K_M.gguf Q4_K_M
```
Test with llama.cpp Metal backend or Kuzco SPM wrapper on device.

### 2.3 — Baseline stock model quality
Run 10 sample problems through stock Qwen3-4B-Instruct with all 20 system prompts. Compare to `reference/sample_takes.json`. This establishes the pre-fine-tuning quality floor.

**GO/NO-GO GATE:** Commit to CoreML or llama.cpp based on conversion success + device performance.

---

## Step 3: SFT Fine-Tuning (PC/WSL2, $0 — local GPU)

Transfer training data to the PC, then run under WSL2.

### 3.0 — Environment setup (one-time)
```bash
# In WSL2 on the RTX 5090 PC
pip install unsloth torch transformers datasets trl accelerate bitsandbytes
# Verify CUDA is visible
python -c "import torch; print(torch.cuda.get_device_name(0))"
```

### 3.1 — Transfer training data to PC
Copy these files from Mac to PC (via scp, shared drive, etc.):
```
data/sft_train.jsonl
data/sft_val.jsonl
data/dpo_train.jsonl
data/dpo_val.jsonl
scripts/training/sft_train.py
scripts/training/dpo_train.py
scripts/training/merge_and_export.py
```

### 3.2 — SFT on Qwen3-4B-Instruct
```bash
python scripts/training/sft_train.py --model 4b
```
- QLoRA: rank 32, alpha 64, all linear layers, bf16
- LR 2e-4, cosine schedule, 3 epochs, max_seq 2048, effective batch 16
- Estimated time: ~2-4 hours on RTX 5090
- Output: `models/er-qwen3-4b-sft/` (LoRA adapter)

### 3.3 — SFT on Qwen3-1.7B-Instruct
```bash
python scripts/training/sft_train.py --model 1.7b
```
- Same config, 5 epochs for smaller model
- Estimated time: ~1-2 hours
- Output: `models/er-qwen3-1.7b-sft/` (LoRA adapter)

---

## Step 4: DPO Alignment + Export (PC/WSL2, $0)

### 4.1 — DPO on Qwen3-4B
```bash
python scripts/training/dpo_train.py --model 4b
```
- Loads SFT adapter as starting point
- Beta 0.1, LR 5e-5, 1 epoch
- Output: `models/er-qwen3-4b-dpo/` (LoRA adapter)

### 4.2 — DPO on Qwen3-1.7B
```bash
python scripts/training/dpo_train.py --model 1.7b
```

### 4.3 — Merge LoRA adapters and export
```bash
python scripts/training/merge_and_export.py --model 4b
python scripts/training/merge_and_export.py --model 1.7b
```
- Merges LoRA into base model, exports safetensors
- Output: `models/er-qwen3-4b-merged/`, `models/er-qwen3-1.7b-merged/`

### 4.4 — Quality evaluation
- Run 50 held-out problems × 20 lenses through both fine-tuned models
- Compare to stock baseline + `reference/sample_takes.json`
- Human review of 20+ takes across all personas
- **Target:** >90% format compliance, recognizable persona voices, problem-specific content
- **ITERATE** steps 3-4 if quality insufficient (expect 1-2 rounds)

---

## Step 5: Model Conversion (Mac, $0)

Transfer merged models back to Mac for CoreML conversion.

### 5.1 — Convert to CoreML via ANEMLL
```bash
./anemll/utils/convert_model.sh --model ./models/er-qwen3-4b-merged --output ./coreml-4b
./anemll/utils/convert_model.sh --model ./models/er-qwen3-1.7b-merged --output ./coreml-1.7b
```
Context window: 1024 tokens (sufficient for system prompt + problem + response).

### 5.2 — GGUF fallback (if CoreML fails)
```bash
python convert_hf_to_gguf.py ./models/er-qwen3-4b-merged --outtype f16
llama-quantize er-qwen3-4b-f16.gguf er-qwen3-4b-Q4_K_M.gguf Q4_K_M
# Repeat for 1.7B
```

### 5.3 — Upload to HuggingFace
- Create repos: `endlessrumination/er-qwen3-4b-coreml` and `er-qwen3-1.7b-coreml`
- Upload with Git LFS
- Note direct download URLs for iOS app

### 5.4 — Create model manifest
JSON manifest embedded in the app with download URLs, SHA256 checksums, file sizes, min RAM tier.

---

## Step 6: iOS App Refactor (Mac)

### New files to create

| File | Purpose |
|------|---------|
| `Services/DeviceCapability.swift` | RAM detection → ModelTier enum (1.7B for ≤6GB, 4B for 8GB+) |
| `Services/ModelDownloadManager.swift` | Background URLSession download, SHA256 verify, resume, progress |
| `Services/InferenceEngine.swift` | ANEMLL/llama.cpp wrapper, `generate(systemPrompt:userMessage:)` |
| `Services/LocalTakeGenerator.swift` | Replaces `APIClient.generateBatch()`, sequential inference per lens |
| `Models/LensPrompts.swift` | All 40 system prompts ported to Swift (**already created**) |

### Files to modify

| File | Changes |
|------|---------|
| `App/AppState.swift` | Add model/inference properties, remove `authToken` |
| `Views/ProblemInputView.swift` | Replace API call with `localTakeGenerator` |
| `Services/SafetyService.swift` | Remove server check, expand client blocklist |
| `Services/SubscriptionManager.swift` | Remove `verifyReceiptOnServer()` |
| `App/EndlessRuminationApp.swift` | Init model download + inference engine |
| `Views/AIConsentView.swift` | Update text to "on-device AI" |
| `Views/TakeCardView.swift` | Remove Haiku/Sonnet badge distinction |
| `Views/OnboardingView.swift` | Expand to multi-screen flow masking model download |
| `Views/LoadingView.swift` | Adjust timing (5-15s/take vs 1.5s from cloud) |
| `project.yml` | Add ANEMLL/llama.cpp dep, bump to v1.0.0 build 15 |

### Files to delete
- `Services/APIClient.swift` — no backend
- `Models/User.swift` — no auth
- `Models/Problem.swift` — no server-side storage

---

## Step 7: Integration Testing (Mac + Devices)

### 7.1 — Simulator testing
- Build and run on iPhone 17 Pro simulator
- Verify onboarding → download → first take generation end-to-end

### 7.2 — Device testing
- iPhone 14 (6GB): verify 1.7B loads, runs, doesn't OOM
- iPhone 15 Pro / 16 (8GB): verify 4B loads, runs at acceptable speed
- Test airplane mode: fully offline after model download
- Measure: battery drain during 20-take session, thermal throttling

### 7.3 — Quality review
- Generate takes for 20 diverse problems across all lenses
- Read through ALL output: format compliance, persona authenticity, specificity
- Compare subjectively to the cloud Sonnet experience
- Identify failure modes: repetition, generic responses, tone drift

---

## Step 8: TestFlight Build (Mac)

```bash
cd ios && xcodegen generate
xcodebuild -scheme EndlessRumination -sdk iphoneos -configuration Release \
  -archivePath /tmp/ER-iOS.xcarchive archive
xcodebuild -exportArchive -archivePath /tmp/ER-iOS.xcarchive \
  -exportOptionsPlist /tmp/ExportOptions.plist -exportPath /tmp/ER-iOS-Export \
  -allowProvisioningUpdates \
  -authenticationKeyPath ~/.appstoreconnect/private_keys/AuthKey_8YM9M9P47X.p8 \
  -authenticationKeyID 8YM9M9P47X \
  -authenticationKeyIssuerID e5829743-777b-4a9f-a968-30a8714fb272
```

### Success criteria
1. App launches, downloads model during onboarding (masked by interactive screens)
2. Offline inference: airplane mode produces takes with no network
3. All 20 base lenses produce recognizable, problem-specific takes
4. Correct model tier selected per device (1.7B on 6GB, 4B on 8GB+)
5. IAP still works (Pro subscription, voice packs via StoreKit 2)
6. Ads display for free tier
7. Safety blocklist rejects harmful input
8. "Your thoughts never leave this device" messaging throughout

---

## Key Risks

| Risk | Mitigation |
|------|-----------|
| ANEMLL Qwen3-4B conversion fails | Step 2 gate; llama.cpp + GGUF fallback is proven |
| Fine-tuned quality below bar | DPO training + iterate; narrow domain helps small models |
| 2-5 min for 20 takes too slow | Show takes progressively; user scrolls while rest generate |
| 1.7B quality notably worse than 4B | Could make model tier a Pro feature |
| App Store rejection | AI consent dialog retained; on-device = simpler privacy story |
| Memory pressure on 6GB devices | `os_proc_available_memory()` check; reduce context; unload between sessions |

---

## File Reference

### Distillation scripts (Mac)
```
scripts/distillation/
├── cost_tracker.py          # Shared $100 budget tracker
├── generate_seeds.py        # Step 1.1 — 200 seed prompts
├── expand_seeds.py          # Step 1.2 — expand to 1200
├── generate_responses.py    # Step 1.3 — teacher responses ($78 budget)
├── filter_quality.py        # Step 1.4 — Haiku scoring ($10 budget)
├── generate_dpo_pairs.py    # Step 1.5 — bad response pairs ($12 budget)
└── format_training_data.py  # Step 1.6 — ChatML conversion
```

### Training scripts (PC/WSL2)
```
scripts/training/
├── sft_train.py             # Steps 3.2-3.3 — QLoRA SFT
├── dpo_train.py             # Steps 4.1-4.2 — DPO alignment
└── merge_and_export.py      # Step 4.3 — merge LoRA + export
```

### Generated data (gitignored)
```
data/
├── seed_prompts.jsonl       # 200 seeds
├── expanded_prompts.jsonl   # 1,197 expanded prompts
├── teacher_responses.jsonl  # Sonnet responses (step 1.3)
├── filtered_responses.jsonl # Quality-filtered (step 1.4)
├── rejected_responses.jsonl # Failed quality filter
├── dpo_pairs.jsonl          # DPO preference pairs (step 1.5)
├── sft_train.jsonl          # ChatML training set
├── sft_val.jsonl            # ChatML validation set
├── dpo_train.jsonl          # DPO training set
├── dpo_val.jsonl            # DPO validation set
└── .pipeline_cost_tracker.json  # Budget tracker
```

### iOS files (new for on-device)
```
ios/EndlessRumination/
├── Models/LensPrompts.swift           # ✅ Created — 40 system prompts
├── Services/DeviceCapability.swift    # To create (step 6)
├── Services/ModelDownloadManager.swift # To create (step 6)
├── Services/InferenceEngine.swift     # To create (step 6)
└── Services/LocalTakeGenerator.swift  # To create (step 6)
```
