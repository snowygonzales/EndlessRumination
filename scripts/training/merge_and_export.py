"""Step 4.3 — Merge LoRA adapters and export full model.

Merges the DPO (or SFT) adapter into the base model and exports
as bf16 safetensors (HuggingFace format) for MLX conversion.

Usage:
    source ~/er-train-venv/bin/activate
    python scripts/training/merge_and_export.py --model 4b
    python scripts/training/merge_and_export.py --model 2b
    python scripts/training/merge_and_export.py --model 4b --sft-only  # skip DPO

Output: models/er-qwen35-{size}-merged/
"""

from __future__ import annotations

import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description="Merge LoRA and export model")
parser.add_argument("--model", choices=["4b", "2b"], default="4b")
parser.add_argument("--sft-only", action="store_true", help="Merge SFT adapter only (skip DPO)")
parser.add_argument("--max-seq-len", type=int, default=2048)

args = parser.parse_args()

# Determine which adapter to merge
if args.sft_only:
    ADAPTER_DIR = Path(f"models/er-qwen35-{args.model}-sft")
else:
    ADAPTER_DIR = Path(f"models/er-qwen35-{args.model}-dpo")
    if not ADAPTER_DIR.exists():
        print(f"DPO adapter not found at {ADAPTER_DIR}, falling back to SFT")
        ADAPTER_DIR = Path(f"models/er-qwen35-{args.model}-sft")

OUTPUT_DIR = Path(f"models/er-qwen35-{args.model}-merged")

if not ADAPTER_DIR.exists():
    print(f"ERROR: Adapter not found at {ADAPTER_DIR}")
    exit(1)

print(f"=" * 60)
print(f"Merging LoRA adapter into base model")
print(f"  Adapter: {ADAPTER_DIR}")
print(f"  Output:  {OUTPUT_DIR}")
print(f"=" * 60)

print("\nLoading libraries...")

from unsloth import FastLanguageModel

print(f"\nLoading model + adapter from {ADAPTER_DIR} in bf16...")

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=str(ADAPTER_DIR),
    max_seq_length=args.max_seq_len,
    load_in_4bit=False,     # bf16, matching training
    dtype="bfloat16",
)

# Merge LoRA weights into base model and save as bf16 safetensors
# Using Unsloth's save_pretrained_merged which handles merge + export cleanly
print(f"\nMerging LoRA adapters and saving to {OUTPUT_DIR}...")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

model.save_pretrained_merged(
    str(OUTPUT_DIR),
    tokenizer,
    save_method="merged_16bit",
)

print(f"\nDone! Full merged model at {OUTPUT_DIR}")
print(f"\nNext steps (on Mac):")
print(f"  MLX convert: python -m mlx_lm.convert --model {OUTPUT_DIR} --quantize --q-bits 4 --q-group-size 64 -o models/er-qwen35-{args.model}-mlx-4bit")
