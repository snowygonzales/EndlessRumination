"""Phase 2.4 — Merge LoRA adapters and export full model.

Merges the DPO (or SFT) adapter into the base model and exports
as full-precision safetensors for subsequent CoreML or GGUF conversion.

Usage:
    python scripts/training/merge_and_export.py --model 4b
    python scripts/training/merge_and_export.py --model 1.7b
    python scripts/training/merge_and_export.py --model 4b --sft-only  # skip DPO

Output: models/er-qwen3-{size}-merged/
"""

from __future__ import annotations

import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description="Merge LoRA and export model")
parser.add_argument("--model", choices=["4b", "1.7b"], default="4b")
parser.add_argument("--sft-only", action="store_true", help="Merge SFT adapter only (skip DPO)")
parser.add_argument("--max-seq-len", type=int, default=2048)

args = parser.parse_args()

# Determine which adapter to merge
if args.sft_only:
    ADAPTER_DIR = Path(f"models/er-qwen3-{args.model}-sft")
else:
    ADAPTER_DIR = Path(f"models/er-qwen3-{args.model}-dpo")
    if not ADAPTER_DIR.exists():
        print(f"DPO adapter not found at {ADAPTER_DIR}, falling back to SFT")
        ADAPTER_DIR = Path(f"models/er-qwen3-{args.model}-sft")

OUTPUT_DIR = Path(f"models/er-qwen3-{args.model}-merged")

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

print(f"\nLoading model + adapter from {ADAPTER_DIR}...")

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=str(ADAPTER_DIR),
    max_seq_length=args.max_seq_len,
    load_in_4bit=True,
    dtype=None,
)

# Merge LoRA weights into base model
print("\nMerging LoRA adapters...")
model = model.merge_and_unload()

# Save merged model as full-precision safetensors
print(f"\nSaving merged model to {OUTPUT_DIR}...")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

model.save_pretrained(str(OUTPUT_DIR))
tokenizer.save_pretrained(str(OUTPUT_DIR))

print(f"\nDone! Full merged model at {OUTPUT_DIR}")
print(f"\nNext steps:")
print(f"  CoreML: ./anemll/utils/convert_model.sh --model {OUTPUT_DIR} --output ./coreml-{args.model}")
print(f"  GGUF:   python convert_hf_to_gguf.py {OUTPUT_DIR} --outtype f16")
print(f"          llama-quantize er-qwen3-{args.model}-f16.gguf er-qwen3-{args.model}-Q4_K_M.gguf Q4_K_M")
