# Experiment: On-Device LLM Inference Pipeline

Full step-by-step guide for fine-tuning **Qwen 3.5** models to replace cloud Claude API with on-device inference via **Apple MLX**. The goal is a fully offline, privacy-first iOS app positioned for Apple App Store featuring.

**Branch:** `experiment/on-device-inference` (cloud API preserved on `master`, tagged `v0.4.0-cloud-api`)

**Hardware:**
- Mac Mini M1 — dataset generation (steps 1-2), model conversion (step 5), iOS build (steps 7-8)
- PC with RTX 5090 (32GB VRAM), WSL2 — fine-tuning (steps 3-4)
- Physical iPhones (iOS 18+) — device testing (step 7)

**Budget:** $100 shared across steps 1.3 + 1.4 + 1.5 (tracked via `data/.pipeline_cost_tracker.json`)

**Key Technology Choices:**
- **Model:** Qwen 3.5 4B only — released March 2, 2026 (2B evaluated and dropped due to insufficient comprehension)
- **Training:** Unsloth with **bf16 LoRA** (NOT QLoRA — Unsloth warns against 4-bit for Qwen 3.5's Gated DeltaNet architecture)
- **Inference:** Apple MLX via mlx-swift — ~40% faster than llama.cpp on Apple Silicon, native Swift API, WWDC 2025 featured
- **Format:** MLX safetensors (4-bit quantized) — ~2.0 GB optimized (vision stripped, vocab pruned)

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

### 1.3 — Generate teacher responses (heaviest step) ✅
```bash
python scripts/distillation/generate_responses.py
```
- For each prompt, generates a take from all 20 base lenses using Sonnet
- Uses exact system prompts from `backend/app/lenses/definitions.py`
- Concurrency: 10 (Tier 2: 90K output tokens/min), resume support via `.generate_responses_progress.json`
- Budget allocation: **$78** (spent: $74.16)
- Output: `data/teacher_responses.jsonl` (14,520 responses, 37 MB)
- Status: **Done** — 650 prompts × 20 lenses, ~170 min

### 1.4 — Quality filter via Haiku ✅
```bash
python scripts/distillation/filter_quality.py
```
- Scores each response on 4 dimensions (1-5) using Haiku: persona authenticity, problem specificity, emotional impact, safety
- Keeps only responses scoring 4+ on ALL dimensions (`format_ok` is soft signal, not hard gate)
- Budget allocation: **$10** (spent: $7.99)
- Concurrency: 10 (reduced from 30 to avoid 529 overloaded errors)
- Output: `data/filtered_responses.jsonl` (8,850 kept, 61% survival) + `data/rejected_responses.jsonl` (5,670)
- Only 15 API scoring failures (0.3%) — rest are legitimate quality rejections
- Status: **Done**
- Note: Lens 8 (CEO, 47 kept) and Lens 18 (Conspiracy Theorist, 59 kept) have low counts due to strict safety scoring

### 1.5 — Generate DPO preference pairs ✅
```bash
python scripts/distillation/generate_dpo_pairs.py
```
- For ~1,900 filtered responses, generates intentionally bad responses using 4 strategies: generic, wrong_persona, format_violation, shallow
- Budget allocation: **$12** (spent: $11.40)
- Output: `data/dpo_pairs.jsonl` (1,900 pairs)
- Status: **Done**

### 1.6 — Format for training ✅
```bash
python scripts/distillation/format_training_data.py
```
- Converts to ChatML format (`<|im_start|>system/user/assistant<|im_end|>`)
- 90/10 train/val split
- No API calls ($0)
- Output: `data/sft_train.jsonl` (7,965), `data/sft_val.jsonl` (885), `data/dpo_train.jsonl` (1,710), `data/dpo_val.jsonl` (190)
- Status: **Done**

### Step 1 Summary
- **Total API spend: $93.55 / $100**
- **8,850 SFT examples** (7,965 train + 885 val)
- **1,900 DPO pairs** (1,710 train + 190 val)
- All 20 lenses represented, ChatML format verified

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

Before training, confirm MLX works with stock Qwen 3.5 models.

### 2.1 — Test MLX inference on Mac ✅
```bash
# Requires Python 3.12+ (system Python 3.9 is too old for latest MLX)
# One-time setup:
brew install python@3.12
/opt/homebrew/opt/python@3.12/bin/python3.12 -m venv .mlx-venv
source .mlx-venv/bin/activate
pip install "mlx-lm @ git+https://github.com/ml-explore/mlx-lm.git"
# Note: pip install mlx-lm (PyPI v0.29.1) does NOT support Qwen 3.5 yet —
# must install from git for mlx-lm 0.30.8+ with qwen3_5 model type support
```

**Results on Mac Mini M1:**

| Model | Tok/s (gen) | Peak Memory | Time (200 tok) |
|-------|-------------|-------------|----------------|
| Qwen3.5-2B-4bit | **43.7** | **1.26 GB** | 5.9s |
| Qwen3.5-4B-4bit | **20.5** | **2.69 GB** | 6.3s |

- Status: **Done** — both models load and generate coherent, persona-differentiated output
- Stock model format compliance is rough (markdown leaks, length issues) — fine-tuning will fix this
- Prompt processing: 67-125 tok/s (fast, system prompt ingestion is negligible)

> **Critical: Thinking mode must be explicitly disabled for Qwen 3.5 4B.** Unlike 2B which has thinking off by default, 4B outputs chain-of-thought reasoning tokens that waste ~100 tokens per response. Fix: `enable_thinking=False` in `apply_chat_template()`. This is essential for both training data format and inference.

> **API change in mlx-lm 0.30+:** `generate()` no longer accepts `temp=` kwarg. Use `sampler=make_sampler(temp=0.7)` from `mlx_lm.sample_utils`.

### 2.2 — Test mlx-swift on physical iPhone
Create a minimal test Xcode project with mlx-swift:
- Add SPM dependency: `https://github.com/ml-explore/mlx-swift.git`
- Add SPM dependency: `https://github.com/ml-explore/mlx-swift-lm.git`
- Load fine-tuned 4B model on device
- **Important:** mlx-swift does NOT work in simulator — physical device only
- Measure: first token latency, tok/s, total memory footprint
- Target: first token <3s, 20+ tok/s generation, <3 GB memory for optimized 4B
- Status: **Pending** — deferred until after fine-tuning (step 2.1 confirms MLX works, device test with fine-tuned model in step 7)

### 2.3 — Baseline stock model quality
Run 10 sample problems through stock Qwen3.5-4B with all 20 system prompts from `backend/app/lenses/definitions.py`. Compare to `reference/sample_takes.json`. This establishes the pre-fine-tuning quality floor.
- Status: **Partial** — tested 4 lenses (Grandma, Stoic, Comedian, Scientist) with 1 problem. Personas are recognizable but format compliance is low. Full 20-lens baseline deferred to step 4.4 (comparison with fine-tuned model).

**GO/NO-GO GATE: ✅ PASSED** — MLX + Qwen 3.5 inference works on Mac M1 at excellent speed and memory. Proceeding to training.

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

### 3.0 — Environment setup (one-time) ✅

**⚠️ RTX 5090 (Blackwell, SM_120) requires special setup:**

```bash
# In WSL2 on the RTX 5090 PC

# 1. Create venv (separate from any Windows Python)
python3 -m venv ~/er-train-venv
source ~/er-train-venv/bin/activate

# 2. Install PyTorch nightly with CUDA 12.8 (stable PyTorch does NOT support Blackwell)
pip install torch --extra-index-url https://download.pytorch.org/whl/cu128

# 3. Install Unsloth (handles transformers dependency internally)
pip install unsloth

# 4. Install remaining deps
pip install datasets trl accelerate bitsandbytes

# 5. Verify CUDA is visible and correct arch
python -c "import torch; print(torch.cuda.get_device_name(0)); print(f'CUDA arch: {torch.cuda.get_device_capability()}')"
# Expected: NVIDIA GeForce RTX 5090, CUDA arch: (12, 0)
```

**Actual installed versions (2026-03-05):**
- PyTorch 2.10.0+cu128
- Triton 3.6.0
- Unsloth 2026.3.3
- datasets, trl, accelerate, bitsandbytes (latest)

**Important notes:**
- **Flash Attention 2/3 do NOT work on Blackwell SM_120.** This is fine — Unsloth uses its own Triton-based attention kernels that bypass Flash Attention entirely.
- **WSL2 memory quirk:** OOM errors can occur even with free VRAM. Start with conservative settings and scale up. Monitor with `nvidia-smi` in a separate terminal.
- **Triton >= 3.3.1** required (supports SM_120). Should install automatically with Unsloth.

### 3.1 — Transfer training data to PC ✅
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

**⚠️ CRITICAL: Train from native Linux filesystem, NOT `/mnt/c/`.**
Running from the Windows mount (`/mnt/c/Users/.../EndlessRumination`) causes severe I/O bottleneck — 100% CPU, ~3% GPU utilization, training speed drops ~10x. Copy data to a native WSL2 path:
```bash
mkdir -p ~/er-training/{data,scripts/training,models}
cp /mnt/c/.../EndlessRumination/data/{sft,dpo}_{train,val}.jsonl ~/er-training/data/
cp /mnt/c/.../EndlessRumination/scripts/training/*.py ~/er-training/scripts/training/
cd ~/er-training
```

### 3.2 — SFT on Qwen3.5-4B ✅
```bash
# ⚠️ Default batch size (2) severely underutilizes RTX 5090 — use batch 4:
python scripts/training/sft_train.py --model 4b --batch-size 4 --grad-accum 4
```
- **bf16 LoRA** (NOT QLoRA): rank 16, alpha 32, target all linear layers (`q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`)
- LR 2e-4, cosine schedule, 3 epochs, max_seq 2048, effective batch 16
- `use_gradient_checkpointing = "unsloth"` (30% VRAM savings)
- Output: `models/er-qwen35-4b-sft/` (LoRA adapter)

**Actual results (2026-03-05):**
- **VRAM: ~21 GB** (with batch-size 4)
- **Power: ~230W**, temperature ~59°C
- **Wall time: ~4 hours** (1,494 steps total, 3 epochs)
- **Adapter size: 82 MB**
- Epoch 1 eval_loss: 0.7573
- **Epoch 2 eval_loss: 0.7313** (best — loaded by `load_best_model_at_end`)
- Epoch 3 eval_loss: 0.7687 (slight overfit)
- Best checkpoint: step 996 (epoch 2)

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

### 3.3 — SFT on Qwen3.5-2B ✅
```bash
# ⚠️ 2B model needs larger batch to saturate GPU. batch-size 8 is stable.
# DO NOT use batch-size 16 — caused full PC shutdown at 270W!
python scripts/training/sft_train.py --model 2b --batch-size 8 --grad-accum 2
```
- Same bf16 LoRA config, 5 epochs for smaller model
- Output: `models/er-qwen35-2b-sft/` (LoRA adapter)

**Actual results (2026-03-06):**
- **VRAM: ~17 GB** (with batch-size 8)
- **Power: ~210-225W**, temperature ~58°C
- **Wall time: ~6 hours** (2,490 steps total, 5 epochs)
- Epoch 1 eval_loss: 0.9393
- **Epoch 2 eval_loss: 0.8904** (best — loaded by `load_best_model_at_end`)
- Epoch 3 eval_loss: 0.9037 (slight overfit)
- Epoch 4 eval_loss: 0.9664 (overfitting)
- Epoch 5 eval_loss: 1.0365 (clear overfit)
- Best checkpoint: step 996 (epoch 2)
- Same pattern as 4B — **epoch 2 is the sweet spot**

**⚠️ Batch size warning:**
- `--batch-size 4`: GPU underutilized (~50W, 5% GPU)
- `--batch-size 8`: Good (~220W, stable) ← **use this**
- `--batch-size 16`: **DANGEROUS** — 270W, caused full PC shutdown/crash

**WSL2 troubleshooting — if OOM despite free VRAM:**
```bash
# Reduce these settings:
--max_seq_length 1024        # down from 2048
--per_device_train_batch_size 1  # down from 2+
--gradient_accumulation_steps 16 # increase to compensate
```

---

## Step 4: DPO Alignment + Export (PC/WSL2, $0)

> **⚠️ CRITICAL BUG: Unsloth cannot be used for DPO on Qwen 3.5.**
>
> Qwen 3.5 registers `model_type: "qwen3_5"` which appears in transformers'
> `MODEL_FOR_IMAGE_TEXT_TO_TEXT_MAPPING_NAMES` (shared with Qwen3.5-VL vision variant).
> Unsloth's patched `DPOTrainer` checks this mapping to decide between `tokenize_row`
> (text path) vs `process_row` (vision path). For text-only Qwen 3.5, the vision path
> crashes with `KeyError: 'images'` because there are no image inputs.
>
> **Workaround:** `dpo_train.py` uses **vanilla transformers + PEFT + TRL** instead of
> Unsloth. The SFT adapter (saved by Unsloth) is loaded via standard `PeftModel.from_pretrained()`.
> This is ~2x slower than Unsloth but DPO is 1 epoch on small data (~1 hour), so acceptable.
>
> Additional fixes needed for vanilla TRL:
> - Use `processing_class=tokenizer` (not `tokenizer=tokenizer` — deprecated in TRL 0.14+)
> - Set `model.warnings_issued = {}` (PeftModel doesn't have this attribute, TRL expects it)
> - Use `attn_implementation="eager"` (Flash Attention incompatible with Blackwell SM_120)
> - Temporarily remove `unsloth` from `sys.modules` before importing `trl` to prevent
>   Unsloth's import hooks from patching `DPOTrainer`

### 4.1 — DPO on Qwen3.5-4B ✅
```bash
python scripts/training/dpo_train.py --model 4b --batch-size 2 --grad-accum 4
```
- Loads SFT adapter via vanilla PEFT (NOT Unsloth — see bug above)
- bf16, Beta 0.1, LR 5e-5, 1 epoch, effective batch 8
- **VRAM: ~22 GB** (DPO needs chosen + rejected forward passes)
- **Power: ~218W**, temperature ~58°C
- **Wall time: ~50 min** (214 steps, 1 epoch)
- Output: `models/er-qwen35-4b-dpo/` (LoRA adapter)
- **Eval loss: 0.0002**, accuracy: 100%, reward margin: 19.0
- Status: **Done** (2026-03-06)

```python
# Key DPO approach (in dpo_train.py):
# 1. Prevent Unsloth from patching TRL
import sys
_unsloth_modules = [k for k in sys.modules if 'unsloth' in k]
_saved_unsloth = {k: sys.modules.pop(k) for k in _unsloth_modules}

# 2. Load model with vanilla transformers + PEFT
from transformers import AutoModelForCausalLM
from peft import PeftModel

model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    attn_implementation="eager",  # No Flash Attention on Blackwell
)
model = PeftModel.from_pretrained(model, str(SFT_ADAPTER), is_trainable=True)
model.warnings_issued = {}  # TRL expects this attribute

# 3. Train with vanilla TRL DPOTrainer
from trl import DPOTrainer, DPOConfig
trainer = DPOTrainer(
    model=model,
    processing_class=tokenizer,  # NOT tokenizer= (deprecated)
    ...
)
```

### 4.2 — DPO on Qwen3.5-2B ✅
```bash
python scripts/training/dpo_train.py --model 2b --batch-size 2 --grad-accum 4
```
- Same vanilla PEFT + TRL approach
- **VRAM: ~15 GB**
- **Power: ~200W**, temperature ~57°C
- **Wall time: ~90 min** (214 steps, 1 epoch)
- Output: `models/er-qwen35-2b-dpo/` (LoRA adapter)
- **Eval loss: 0.0004**, accuracy: 100%, reward margin: 18.3
- Status: **Done** (2026-03-06)

### 4.3 — Merge LoRA adapters and export to HuggingFace format ✅
```bash
python scripts/training/merge_and_export.py --model 4b
python scripts/training/merge_and_export.py --model 2b
```
- Merges LoRA into base model via Unsloth's `save_pretrained_merged("merged_16bit")`
- Exports as bf16 safetensors (HuggingFace format)
- Output: `models/er-qwen35-4b-merged/` (8.7 GB), `models/er-qwen35-2b-merged/` (4.3 GB)
- Status: **Done** (2026-03-06)

> **Known Unsloth quirk:** `save_pretrained_merged` may re-download base model weights into a `.cache/` folder inside the output directory instead of reusing the HF cache. This is a disk space annoyance (~8 GB for 4B), not a correctness issue. Delete the `.cache/` folder after export if disk is tight.

> **Post-merge cleanup:** Intermediate artifacts (SFT adapters, DPO adapters, all checkpoints) were deleted after successful merge. Only the two merged models remain on the PC. HF cache (~14 GB) retained in case retraining is needed.

### 4.4 — Quality evaluation (Gradio UI)

**Tool:** `scripts/evaluation/eval_ui.py` — Gradio web UI accessible from any device on LAN.

```bash
# Install Gradio (one-time)
pip install gradio

# With DPO adapter (before merge):
python scripts/evaluation/eval_ui.py --model-path models/er-qwen35-4b-dpo --adapter

# With merged model (after merge_and_export.py):
python scripts/evaluation/eval_ui.py --model-path models/er-qwen35-4b-merged

# Side-by-side fine-tuned vs stock:
python scripts/evaluation/eval_ui.py --model-path models/er-qwen35-4b-dpo --adapter --compare
```

**Features:**
- **Interactive tab:** Pick any of all 40 lenses, type a worry, generate + read the take
- **Side-by-side tab:** Fine-tuned vs stock model output for direct comparison (requires `--compare`)
- **Batch tab:** Auto-run 10 held-out prompts × selected lenses, get format compliance stats
- **Ratings tab:** 1-5 human ratings saved to `data/eval_ratings.jsonl`
- Format compliance auto-check (headline length, blank line, body length, markdown/label detection)
- Accessible at `http://<PC_IP>:7860` from any device on LAN

**Evaluation criteria:**
- **Format compliance:** >90% of takes follow headline + blank line + body format
- **Persona authenticity:** each lens sounds distinctly like its character
- **Problem specificity:** takes reference the user's actual problem, not generic advice
- **Compare to:** `reference/sample_takes.json` (cloud Sonnet quality bar)

**Evaluation Results:**
- **4B with top-k=40:** Acceptable quality — format compliance good, persona somewhat generic vs Sonnet but coherent and problem-specific
- **2B:** DROPPED — fundamental comprehension failures (misattributes subject/object in multi-clause sentences). SFT eval loss 0.89 vs 4B's 0.73 reflects insufficient capacity for this use case.

**Decision: 4B only.** Minimum viable device is iPhone 15 Pro (8 GB), with optimization targeting iPhone 15 base (6 GB).

---

## Step 4.5: Optimize Model for 6GB Devices ✅

Strip unnecessary components to minimize on-device memory footprint.

```bash
source ~/er-train-venv/bin/activate
cd ~/er-training

# Strip vision encoder (667 MB) + prune non-English vocab (554 MB)
python scripts/training/optimize_for_device.py --model 4b --prune-vocab
```

**Optimizations applied:**
1. **Vision encoder stripped:** Unsloth's merge included a full 24-layer vision encoder from Qwen 3.5 VL (shared model_type). Removed 333M params (667 MB in bf16).
2. **Vocabulary pruned:** 248,320 → 140,032 tokens (56.4%). Removed CJK, Cyrillic, Arabic, Thai, Korean, Devanagari tokens. Kept all ASCII/Latin tokens + tokens found in training data.

**Results:**
- Original merged: 9.32 GB (bf16)
- Optimized: 8.10 GB (bf16), saving 1.22 GB (13.1%)
- **4-bit estimate: ~2.0 GB** (vs ~2.3 GB without optimization)
- Runtime memory estimate: ~2.4 GB total (weights + recurrent state + activations)
- Target: fits in 6GB device with ~3 GB available after iOS overhead

**Recommended generation params (4B):** temperature=0.7, top_k=40, top_p=0.95

---

## Step 5: Model Conversion to MLX (Mac, $0)

Convert optimized HuggingFace model to MLX 4-bit format for iOS deployment.

### 5.1 — Install mlx-lm (if not already installed)
```bash
pip install mlx-lm
```

### 5.2 — Convert to MLX 4-bit format
```bash
# Convert optimized 4B model
python -m mlx_lm.convert \
    --model ./models/er-qwen35-4b-optimized \
    --quantize \
    --q-bits 4 \
    --q-group-size 64 \
    -o ./models/er-qwen35-4b-mlx-4bit
```

Expected output size:
- 4B optimized 4-bit: **~2.0 GB**

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
```

---

## Step 6: iOS App Refactor (Mac)

**Minimum iOS version change: iOS 17 → iOS 18** (required by mlx-swift for Gated DeltaNet Metal kernels).

### New files to create

| File | Purpose |
|------|---------|
| `Services/DeviceCapability.swift` | RAM check + memory budget validation for optimized 4B model |
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

    func loadModel() async throws {
        let config = ModelConfiguration(
            id: "endlessrumination/er-qwen35-4b-mlx-4bit"
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
- Subtle progress bar at bottom. Model download ~2.0 GB.
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

| Device | RAM | Model | Key Test |
|--------|-----|-------|----------|
| iPhone 15 (A16, 6GB) | 6 GB | 4B optimized (~2.0 GB) | Memory pressure, no OOM on 6GB |
| iPhone 15 Pro (A17, 8GB) | 8 GB | 4B optimized (~2.0 GB) | Speed, quality, comfortable headroom |
| iPhone 16 Pro (A18, 8GB) | 8 GB | 4B optimized (~2.0 GB) | Best-case performance |

For each device:
- First-launch: onboarding + download + first generation end-to-end
- Test airplane mode: fully offline after model downloaded
- Generate 20 takes for a single problem — measure total time
- Monitor memory with Xcode Instruments (check `increased-memory-limit` is active)
- Measure: battery drain during 20-take session, thermal throttling

**Performance targets:**

| Metric | 4B on A16 (6GB) | 4B on A17 Pro (8GB) |
|--------|------------------|---------------------|
| Tok/s generation | 15-25 | 20-35 |
| Time per take (~200 tokens) | 8-13s | 6-10s |
| Total 20 takes | 2.5-4 min | 2-3.5 min |
| Peak memory | <3 GB | <3.5 GB |

### 7.2 — Quality review
- Generate takes for 20 diverse problems across all 20 lenses
- Read through ALL output: format compliance, persona authenticity, specificity
- Compare subjectively to the cloud Sonnet experience
- Identify failure modes: repetition, generic responses, tone drift
- **6GB vs 8GB device comparison** — verify optimized 4B runs without OOM on 6GB devices

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
4. Optimized 4B model runs on all target devices (6GB+)
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
| RTX 5090 power shutdown at high batch sizes | **Resolved** | 2B with batch-size 16 drew 270W and crashed the PC. Keep batch-size ≤8 for 2B, ≤4 for 4B. Monitor with `nvidia-smi` |
| Fine-tuned Qwen 3.5 → MLX conversion untested | Low | Individual steps all confirmed; first end-to-end may hit minor config issues. Optimized model has vision encoder stripped + vocab pruned — verify MLX converter handles this |
| Qwen 3.5 QLoRA quality degradation | None | Using bf16 LoRA as Unsloth recommends |
| Unsloth DPOTrainer crashes on Qwen 3.5 | **Resolved** | `qwen3_5` model_type is in vision model mapping → DPOTrainer uses vision codepath → `KeyError: 'images'`. Fix: use vanilla transformers + PEFT + TRL for DPO (skip Unsloth). See step 4 notes |
| 4B model on 6GB iPhones | Medium | Optimized model (~2.0 GB at 4-bit) + `increased-memory-limit` entitlement; monitor with Instruments. If OOM, try 3-bit quantization (~1.7 GB) |
| 2B model quality | **Resolved — dropped** | 2B has fundamental comprehension failures (misattributes subject/object). Going 4B-only for all devices |
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
├── merge_and_export.py      # Step 4.3 — merge LoRA + export to HF format
└── optimize_for_device.py   # Step 4.5 — strip vision encoder + prune vocab
```

### Evaluation scripts (PC/WSL2)
```
scripts/evaluation/
└── eval_ui.py               # Step 4.4 — Gradio web UI for human quality eval
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
├── er-qwen35-4b-sft/       # LoRA adapter after SFT (step 3.2) — cleaned up
├── er-qwen35-4b-dpo/       # LoRA adapter after DPO (step 4.1) — cleaned up
├── er-qwen35-4b-merged/    # Full merged model, HF format (step 4.3) — 8.7 GB
├── er-qwen35-4b-optimized/ # Vision stripped + vocab pruned (step 4.5) — 8.1 GB
└── er-qwen35-4b-mlx-4bit/  # MLX 4-bit quantized (step 5.2) — ~2.0 GB
```

> **2B models dropped.** Qwen 3.5 2B had fundamental comprehension failures — misattributing subject/object in multi-clause user input. SFT eval loss 0.89 (vs 4B's 0.73) reflects insufficient capacity for this use case. All 2B artifacts deleted.

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
endlessrumination/er-qwen35-4b-mlx-4bit  # Optimized 4B model for all devices (~2.0 GB)
```

---

## Technology Stack Summary

| Component | Old (Cloud) | New (On-Device) |
|-----------|------------|-----------------|
| Model | Claude Sonnet/Haiku | Qwen 3.5 4B, fine-tuned + optimized |
| Training | N/A | Unsloth, bf16 LoRA, RTX 5090/WSL2 |
| Inference | Anthropic API (SSE) | Apple MLX via mlx-swift |
| Model format | N/A | MLX safetensors (4-bit) |
| iOS framework | URLSession HTTP | mlx-swift + mlx-swift-lm |
| Min iOS | iOS 17 | iOS 18 |
| Privacy | "We process your data securely" | "Your thoughts never leave this device" |
| Cost per use | ~$0.01-0.12 | $0 (on-device) |
| Backend | FastAPI + PostgreSQL + Redis | None |
| Latency | 1.5s/take (cloud) | 5-10s/take (on-device) |
