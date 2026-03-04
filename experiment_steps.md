# Experiment: On-Device LLM Inference Pipeline

Full step-by-step guide for fine-tuning **Qwen 3.5** models to replace cloud Claude API with on-device inference via **Apple MLX**. The goal is a fully offline, privacy-first iOS app positioned for Apple App Store featuring.

**Branch:** `experiment/on-device-inference` (cloud API preserved on `master`, tagged `v0.4.0-cloud-api`)

**Hardware:**
- Mac Mini M1 — dataset generation (steps 1-2), model conversion (step 5), iOS build (steps 7-8)
- PC with RTX 5090 (32GB VRAM), WSL2 — fine-tuning (steps 3-4)
- Physical iPhones (iOS 18+) — device testing (step 7)

**Budget:** $100 shared across steps 1.3 + 1.4 + 1.5 (tracked via `data/.pipeline_cost_tracker.json`)

**Key Technology Choices:**
- **Model:** Qwen 3.5 (2B for ≤6GB devices, 4B for 8GB+ devices) — released March 2, 2026
- **Training:** Unsloth with **bf16 LoRA** (NOT QLoRA — Unsloth warns against 4-bit for Qwen 3.5's Gated DeltaNet architecture)
- **Inference:** Apple MLX via mlx-swift — ~40% faster than llama.cpp on Apple Silicon, native Swift API, WWDC 2025 featured
- **Format:** MLX safetensors (4-bit quantized) — ~1.5 GB for 2B, ~2.5 GB for 4B

---

## Step 1: Dataset Generation (Mac, ~$100 API cost)

All scripts run from the project root with the backend venv active:
```bash
cd EndlessRumination
source backend/.venv/bin/activate
```

> **Note:** Training data is model-agnostic — ChatML format works for both Qwen 3.0 and 3.5. No changes needed to step 1 for the Qwen 3.5 switch.

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
- Output: `data/expanded_prompts.jsonl` (1,197 entries after dedup)
- Cost: ~$5
- Status: **Done** (1,197 prompts)

### 1.3 — Generate teacher responses (heaviest step)
```bash
python scripts/distillation/generate_responses.py
```
- For each prompt, generates a take from all 20 base lenses using Sonnet
- Uses exact system prompts from `backend/app/lenses/definitions.py`
- Concurrency: 10 (Tier 2: 90K output tokens/min), resume support via `.generate_responses_progress.json`
- Budget allocation: **$78** (generates ~650 prompts × 20 lenses = ~13,000 API calls)
- Output: `data/teacher_responses.jsonl`
- Time: ~1-2 hours at concurrency 10

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

Before training, confirm MLX works with stock Qwen 3.5 models on physical iPhones.

### 2.1 — Test MLX inference on Mac
```bash
# Install mlx-lm
pip install mlx-lm

# Test stock Qwen 3.5 models
python -m mlx_lm.generate \
    --model mlx-community/Qwen3.5-2B-4bit \
    --prompt "I'm worried about losing my job" \
    --max-tokens 200

python -m mlx_lm.generate \
    --model mlx-community/Qwen3.5-4B-4bit \
    --prompt "I'm worried about losing my job" \
    --max-tokens 200
```
- Verify model loads and generates coherent text
- Measure tok/s on Mac Mini M1 (baseline reference)

### 2.2 — Test mlx-swift on physical iPhone
Create a minimal test Xcode project with mlx-swift:
- Add SPM dependency: `https://github.com/ml-explore/mlx-swift.git`
- Add SPM dependency: `https://github.com/ml-explore/mlx-swift-lm.git`
- Load `mlx-community/Qwen3.5-2B-4bit` on device
- **Important:** mlx-swift does NOT work in simulator — physical device only
- Measure: first token latency, tok/s, total memory footprint
- Target: first token <3s, 20+ tok/s generation, <2 GB memory for 2B

### 2.3 — Baseline stock model quality
Run 10 sample problems through stock Qwen3.5-4B with all 20 system prompts from `backend/app/lenses/definitions.py`. Compare to `reference/sample_takes.json`. This establishes the pre-fine-tuning quality floor.

> **Note on thinking mode:** Qwen 3.5 small models (0.8B, 2B, 4B) have reasoning/thinking mode **disabled by default**. For our use case (short persona responses, not reasoning tasks) this is ideal — no special handling needed. Do NOT enable thinking mode.

**GO/NO-GO GATE:** Confirm MLX + Qwen 3.5 inference works on physical iPhone at acceptable speed and memory.

### 2.4 — Fallback: llama.cpp + GGUF
If MLX has issues, llama.cpp fully supports Qwen 3.5 (merged Feb 10, 2026):
```bash
# Pre-quantized GGUFs available:
# https://huggingface.co/unsloth/Qwen3.5-4B-GGUF (Q4_K_M ~2.7 GB)
# https://huggingface.co/unsloth/Qwen3.5-2B-GGUF (Q4_K_M ~1.4 GB)
```
Test with llama.cpp Metal backend or Kuzco SPM wrapper on device. ~40% slower than MLX but proven in production.

---

## Step 3: SFT Fine-Tuning (PC/WSL2, $0 — local GPU)

Transfer training data to the PC, then run under WSL2.

### 3.0 — Environment setup (one-time)

**⚠️ RTX 5090 (Blackwell, SM_120) requires special setup:**

```bash
# In WSL2 on the RTX 5090 PC

# 1. Install PyTorch nightly with CUDA 12.8 (stable PyTorch does NOT support Blackwell)
pip install torch --extra-index-url https://download.pytorch.org/whl/cu128

# 2. Install Unsloth (handles transformers dependency internally)
pip install unsloth

# 3. Install remaining deps
pip install datasets trl accelerate bitsandbytes

# 4. Verify CUDA is visible and correct arch
python -c "import torch; print(torch.cuda.get_device_name(0)); print(f'CUDA arch: {torch.cuda.get_device_capability()}')"
# Expected: NVIDIA GeForce RTX 5090, CUDA arch: (12, 0)
```

**Important notes:**
- **Flash Attention 2/3 do NOT work on Blackwell SM_120.** This is fine — Unsloth uses its own Triton-based attention kernels that bypass Flash Attention entirely.
- **WSL2 memory quirk:** OOM errors can occur even with free VRAM. Start with conservative settings and scale up. Monitor with `nvidia-smi` in a separate terminal.
- **Triton >= 3.3.1** required (supports SM_120). Should install automatically with Unsloth.

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

### 3.2 — SFT on Qwen3.5-4B
```bash
python scripts/training/sft_train.py --model 4b
```
- **bf16 LoRA** (NOT QLoRA): rank 16, alpha 32, target all linear layers (`q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`)
- LR 2e-4, cosine schedule, 3 epochs, max_seq 2048, effective batch 16
- `use_gradient_checkpointing = "unsloth"` (30% VRAM savings)
- **Estimated VRAM: ~10 GB** (leaves 22 GB headroom on 32 GB card)
- Estimated time: ~2-4 hours on RTX 5090
- Output: `models/er-qwen35-4b-sft/` (LoRA adapter)

```python
# Key training config (in sft_train.py):
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen3.5-4B",
    max_seq_length=2048,
    load_in_4bit=False,     # DO NOT use QLoRA for Qwen 3.5
    dtype="bfloat16",
)

model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                     "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
)
```

### 3.3 — SFT on Qwen3.5-2B
```bash
python scripts/training/sft_train.py --model 2b
```
- Same bf16 LoRA config, 5 epochs for smaller model
- **Estimated VRAM: ~5 GB**
- Estimated time: ~1-2 hours
- Output: `models/er-qwen35-2b-sft/` (LoRA adapter)

**WSL2 troubleshooting — if OOM despite free VRAM:**
```bash
# Reduce these settings:
--max_seq_length 1024        # down from 2048
--per_device_train_batch_size 1  # down from 2+
--gradient_accumulation_steps 16 # increase to compensate
```

---

## Step 4: DPO Alignment + Export (PC/WSL2, $0)

### 4.1 — DPO on Qwen3.5-4B
```bash
python scripts/training/dpo_train.py --model 4b
```
- Loads SFT adapter as starting point
- bf16 LoRA, Beta 0.1, LR 5e-5, 1 epoch
- **Estimated VRAM: ~15-20 GB** (DPO needs chosen + rejected = ~1.5-2x SFT)
- Output: `models/er-qwen35-4b-dpo/` (LoRA adapter)

### 4.2 — DPO on Qwen3.5-2B
```bash
python scripts/training/dpo_train.py --model 2b
```
- **Estimated VRAM: ~8 GB**
- Output: `models/er-qwen35-2b-dpo/` (LoRA adapter)

### 4.3 — Merge LoRA adapters and export to HuggingFace format
```bash
python scripts/training/merge_and_export.py --model 4b
python scripts/training/merge_and_export.py --model 2b
```
- Merges LoRA into base model via Unsloth's `save_pretrained_merged("merged_16bit")`
- Exports as bf16 safetensors (HuggingFace format)
- Output: `models/er-qwen35-4b-merged/`, `models/er-qwen35-2b-merged/`

> **Known Unsloth quirk:** `save_pretrained_merged` may re-download base model weights into a `.cache/` folder inside the output directory instead of reusing the HF cache. This is a disk space annoyance (~8 GB for 4B), not a correctness issue. Delete the `.cache/` folder after export if disk is tight.

### 4.4 — Quality evaluation
- Run 50 held-out problems × 20 lenses through both fine-tuned models
- Compare to stock baseline + `reference/sample_takes.json`
- Human review of 20+ takes across all personas
- **Target:** >90% format compliance, recognizable persona voices, problem-specific content
- **ITERATE** steps 3-4 if quality insufficient (expect 1-2 rounds)

---

## Step 5: Model Conversion to MLX (Mac or PC, $0)

Convert merged HuggingFace models to MLX 4-bit format for iOS deployment.

> This can run on either Mac or PC. Mac is simpler (MLX is Apple-native). On PC, `mlx-lm` works in regular Python but won't use GPU acceleration for conversion.

### 5.1 — Install mlx-lm (if not already installed)
```bash
pip install mlx-lm
```

### 5.2 — Convert to MLX 4-bit format
```bash
# Convert 4B model
python -m mlx_lm.convert \
    --model ./models/er-qwen35-4b-merged \
    --quantize \
    --q-bits 4 \
    --q-group-size 64 \
    -o ./models/er-qwen35-4b-mlx-4bit

# Convert 2B model
python -m mlx_lm.convert \
    --model ./models/er-qwen35-2b-merged \
    --quantize \
    --q-bits 4 \
    --q-group-size 64 \
    -o ./models/er-qwen35-2b-mlx-4bit
```

Expected output sizes:
- 2B 4-bit: **~1.5 GB**
- 4B 4-bit: **~2.5 GB**

### 5.3 — Verify MLX inference on converted models
```bash
python -m mlx_lm.generate \
    --model ./models/er-qwen35-4b-mlx-4bit \
    --prompt "I'm worried about losing my job" \
    --max-tokens 200
```
Verify output quality matches the merged bf16 model (quantization should not noticeably degrade output).

### 5.4 — Upload to HuggingFace
```bash
# Option A: Use mlx_lm.convert --upload-repo to convert + upload in one step
python -m mlx_lm.convert \
    --model ./models/er-qwen35-4b-merged \
    --quantize --q-bits 4 --q-group-size 64 \
    --upload-repo endlessrumination/er-qwen35-4b-mlx-4bit

python -m mlx_lm.convert \
    --model ./models/er-qwen35-2b-merged \
    --quantize --q-bits 4 --q-group-size 64 \
    --upload-repo endlessrumination/er-qwen35-2b-mlx-4bit

# Option B: Manual upload with huggingface-cli
huggingface-cli upload endlessrumination/er-qwen35-4b-mlx-4bit ./models/er-qwen35-4b-mlx-4bit
```

> **Note:** mlx-swift's `ModelConfiguration` downloads directly from any HuggingFace repo. No separate manifest file is needed — just point to the repo ID.

### 5.5 — GGUF fallback (if MLX has issues)
If MLX inference has problems on device, fall back to llama.cpp GGUF:
```bash
# Install llama.cpp
git clone https://github.com/ggml-org/llama.cpp && cd llama.cpp && make

# Convert merged model to GGUF
python convert_hf_to_gguf.py ./models/er-qwen35-4b-merged --outtype f16
./llama-quantize er-qwen35-4b-f16.gguf er-qwen35-4b-Q4_K_M.gguf Q4_K_M
# Repeat for 2B
```

---

## Step 6: iOS App Refactor (Mac)

**Minimum iOS version change: iOS 17 → iOS 18** (required by mlx-swift for Gated DeltaNet Metal kernels).

### New files to create

| File | Purpose |
|------|---------|
| `Services/DeviceCapability.swift` | RAM detection → ModelTier enum (2B for ≤6GB, 4B for 8GB+) |
| `Services/InferenceEngine.swift` | MLX wrapper via mlx-swift-lm, `generate(systemPrompt:userMessage:) async -> String` |
| `Services/LocalTakeGenerator.swift` | Replaces `APIClient.generateBatch()`, sequential inference per lens |
| `Models/LensPrompts.swift` | All 40 system prompts ported to Swift (**already created**) |

> **ModelDownloadManager is NOT needed** — mlx-swift's `LLMModelFactory` handles HuggingFace download, caching, and progress reporting natively.

### InferenceEngine core code (mlx-swift)

```swift
import MLXLLM
import MLXLMCommon

@Observable class InferenceEngine {
    private var modelContainer: ModelContainer?
    var isLoaded = false

    func loadModel(tier: ModelTier) async throws {
        let config = ModelConfiguration(
            id: tier == .large
                ? "endlessrumination/er-qwen35-4b-mlx-4bit"
                : "endlessrumination/er-qwen35-2b-mlx-4bit"
        )
        modelContainer = try await LLMModelFactory.shared.loadContainer(
            configuration: config
        ) { progress in
            // progress.fractionCompleted — wire to onboarding UI
        }
        isLoaded = true
    }

    func generate(systemPrompt: String, userMessage: String) async throws -> String {
        guard let container = modelContainer else { throw InferenceError.modelNotLoaded }
        let messages: [[String: String]] = [
            ["role": "system", "content": systemPrompt],
            ["role": "user", "content": userMessage],
        ]
        return try await container.perform { context in
            let input = try await context.processor.prepare(
                input: .init(messages: messages)
            )
            var output = ""
            _ = try MLXLMCommon.generate(
                input: input,
                parameters: GenerateParameters(temperature: 0.7),
                context: context
            ) { tokens in
                output = context.tokenizer.decode(tokens)
                return .more
            }
            return output
        }
    }
}
```

### Files to modify

| File | Changes |
|------|---------|
| `App/AppState.swift` | Add `inferenceEngine`, `localTakeGenerator`, `isModelReady` — remove `authToken` |
| `Views/ProblemInputView.swift` | Replace API call with `localTakeGenerator.generateTakes()` |
| `Services/SafetyService.swift` | Remove server check, expand client blocklist |
| `Services/SubscriptionManager.swift` | Remove `verifyReceiptOnServer()` |
| `App/EndlessRuminationApp.swift` | Init InferenceEngine, trigger model download in `.task` |
| `Views/AIConsentView.swift` | Update text to "on-device AI running entirely on your iPhone" |
| `Views/TakeCardView.swift` | Remove Haiku/Sonnet badge distinction (all takes same model) |
| `Views/OnboardingView.swift` | Expand to multi-screen flow masking model download (see below) |
| `Views/LoadingView.swift` | Adjust timing (5-7s/take via MLX vs 1.5s from cloud) |
| `project.yml` | Add mlx-swift + mlx-swift-lm SPM deps, bump to v1.0.0 build 15, set iOS 18 minimum, add `increased-memory-limit` entitlement |

### Entitlements required
```xml
<!-- EndlessRumination.entitlements -->
<key>com.apple.developer.kernel.increased-memory-limit</key>
<true/>
```
This roughly doubles available memory on 8GB devices (~2-3 GB → ~4-6 GB). Essential for the 4B model.

### Onboarding flow (masks model download)
1. "How It Works" (existing)
2. "What's on your mind?" — worry category picker
3. "Meet your advisors" — persona preview with sample takes
4. "Your thoughts stay private" — privacy explainer (key marketing message)
5. "You're all set!" — appears when download completes
- Subtle progress bar at bottom. 2B downloads ~1.5 GB, 4B downloads ~2.5 GB.
- mlx-swift's `LLMModelFactory.loadContainer` provides `Progress` callback natively.

### Files to delete
- `Services/APIClient.swift` — no backend
- `Models/User.swift` — no auth
- `Models/Problem.swift` — no server-side storage

### Simulator development strategy
mlx-swift does NOT work in the iOS Simulator (requires Metal on physical device). Strategy:
- Create a `MockInferenceEngine` conforming to the same protocol
- Returns canned responses from `reference/sample_takes.json` in simulator builds
- Use `#if targetEnvironment(simulator)` to swap implementations
- All UI development and testing works on simulator; inference testing on physical device only

---

## Step 7: Integration Testing (Mac + Physical Devices)

> **No simulator testing for inference** — mlx-swift requires physical device.

### 7.1 — Device testing matrix

| Device | RAM | Model Tier | Key Test |
|--------|-----|------------|----------|
| iPhone 14 Pro (A16, 6GB) | 6 GB | 2B (~1.5 GB) | Memory pressure, no OOM |
| iPhone 15 Pro (A17, 8GB) | 8 GB | 4B (~2.5 GB) | Speed, quality |
| iPhone 16 Pro (A18, 8GB) | 8 GB | 4B (~2.5 GB) | Best-case performance |

For each device:
- First-launch: onboarding + download + first generation end-to-end
- Test airplane mode: fully offline after model downloaded
- Generate 20 takes for a single problem — measure total time
- Monitor memory with Xcode Instruments (check `increased-memory-limit` is active)
- Measure: battery drain during 20-take session, thermal throttling

**Performance targets:**

| Metric | 2B on A16 | 4B on A17 Pro |
|--------|-----------|---------------|
| Tok/s generation | 30-50 | 20-35 |
| Time per take (~200 tokens) | 4-7s | 6-10s |
| Total 20 takes | 1.5-2.5 min | 2-3.5 min |
| Peak memory | <2.5 GB | <4 GB |

### 7.2 — Quality review
- Generate takes for 20 diverse problems across all 20 lenses
- Read through ALL output: format compliance, persona authenticity, specificity
- Compare subjectively to the cloud Sonnet experience
- Identify failure modes: repetition, generic responses, tone drift
- **2B vs 4B quality comparison** — if 2B is notably worse, consider making 4B-only a Pro feature

### 7.3 — Edge cases
- What happens if model download is interrupted? (Resume support)
- What happens if device runs low on storage? (Graceful error)
- App backgrounding during inference — does it resume correctly?
- Multiple rapid submissions — queue management

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
4. Correct model tier selected per device (2B on ≤6GB, 4B on 8GB+)
5. IAP still works (Pro subscription, voice packs via StoreKit 2)
6. Ads display for free tier
7. Safety blocklist rejects harmful input
8. "Your thoughts never leave this device" messaging throughout
9. `increased-memory-limit` entitlement is active (verify in Xcode console)
10. No memory warnings or OOM crashes during 20-take generation

---

## Key Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| PyTorch nightly instability on Blackwell | Medium | Pin a working nightly version once found; NVIDIA has published Unsloth+5090 benchmarks confirming it works |
| Flash Attention incompatible with SM_120 | None | Unsloth uses Triton-based kernels; FA is not needed |
| WSL2 phantom OOM errors | Medium | Start conservative (batch 1, seq 1024), scale up; native Linux dual-boot as escape hatch |
| Fine-tuned Qwen 3.5 → MLX conversion untested | Low | Individual steps all confirmed; first end-to-end may hit minor config issues |
| Qwen 3.5 QLoRA quality degradation | None | Using bf16 LoRA as Unsloth recommends |
| 4B model memory pressure on 8GB iPhones | Medium | `increased-memory-limit` entitlement; 2B fallback tier; monitor with Instruments |
| 2B quality notably worse than 4B | Medium | DPO training helps; could make model tier a Pro feature |
| mlx-swift no simulator support | Low | Mock inference engine for simulator builds; physical device for inference testing |
| iOS 18 minimum (was iOS 17) | Low | iPhone 12+ supports iOS 18; older devices already marginal for LLM inference |
| App Store rejection | Low | AI consent dialog retained; on-device = simpler privacy story; Apple's own MLX = good optics |

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
├── sft_train.py             # Steps 3.2-3.3 — bf16 LoRA SFT
├── dpo_train.py             # Steps 4.1-4.2 — DPO alignment
└── merge_and_export.py      # Step 4.3 — merge LoRA + export to HF format
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

### Models (gitignored, generated on PC)
```
models/
├── er-qwen35-4b-sft/       # LoRA adapter after SFT (step 3.2)
├── er-qwen35-2b-sft/       # LoRA adapter after SFT (step 3.3)
├── er-qwen35-4b-dpo/       # LoRA adapter after DPO (step 4.1)
├── er-qwen35-2b-dpo/       # LoRA adapter after DPO (step 4.2)
├── er-qwen35-4b-merged/    # Full merged model, HF format (step 4.3)
├── er-qwen35-2b-merged/    # Full merged model, HF format (step 4.3)
├── er-qwen35-4b-mlx-4bit/  # MLX 4-bit quantized (step 5.2)
└── er-qwen35-2b-mlx-4bit/  # MLX 4-bit quantized (step 5.2)
```

### iOS files (new/modified for on-device)
```
ios/EndlessRumination/
├── Models/LensPrompts.swift           # ✅ Created — 40 system prompts
├── Services/DeviceCapability.swift    # To create (step 6) — RAM → model tier
├── Services/InferenceEngine.swift     # To create (step 6) — mlx-swift wrapper
└── Services/LocalTakeGenerator.swift  # To create (step 6) — replaces APIClient
```

### HuggingFace repos (created in step 5.4)
```
endlessrumination/er-qwen35-4b-mlx-4bit  # 4B model for 8GB+ devices (~2.5 GB)
endlessrumination/er-qwen35-2b-mlx-4bit  # 2B model for ≤6GB devices (~1.5 GB)
```

---

## Technology Stack Summary

| Component | Old (Cloud) | New (On-Device) |
|-----------|------------|-----------------|
| Model | Claude Sonnet/Haiku | Qwen 3.5 (2B + 4B), fine-tuned |
| Training | N/A | Unsloth, bf16 LoRA, RTX 5090/WSL2 |
| Inference | Anthropic API (SSE) | Apple MLX via mlx-swift |
| Model format | N/A | MLX safetensors (4-bit) |
| iOS framework | URLSession HTTP | mlx-swift + mlx-swift-lm |
| Min iOS | iOS 17 | iOS 18 |
| Privacy | "We process your data securely" | "Your thoughts never leave this device" |
| Cost per use | ~$0.01-0.12 | $0 (on-device) |
| Backend | FastAPI + PostgreSQL + Redis | None |
| Latency | 1.5s/take (cloud) | 5-10s/take (on-device) |
