"""Step 4.1/4.2 — DPO training on top of SFT adapter.

Direct Preference Optimization teaches the model what "good" looks like
relative to "bad" — better than SFT alone for style/quality alignment.

Run this on the RTX 5090 PC (32GB VRAM) under WSL2.

Usage:
    source ~/er-train-venv/bin/activate
    python scripts/training/dpo_train.py --model 4b
    python scripts/training/dpo_train.py --model 2b

Input:  data/dpo_train.jsonl, data/dpo_val.jsonl,
        models/er-qwen35-{size}-sft/ (SFT adapter)
Output: models/er-qwen35-{size}-dpo/
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description="DPO training for Endless Rumination")
parser.add_argument("--model", choices=["4b", "2b"], default="4b")
parser.add_argument("--beta", type=float, default=0.1, help="DPO beta parameter")
parser.add_argument("--lr", type=float, default=5e-5, help="Learning rate")
parser.add_argument("--epochs", type=int, default=1, help="DPO epochs")
parser.add_argument("--batch-size", type=int, default=2, help="Per-device batch size")
parser.add_argument("--grad-accum", type=int, default=4, help="Gradient accumulation")

args = parser.parse_args()

SFT_ADAPTER = Path(f"models/er-qwen35-{args.model}-sft")
OUTPUT_DIR = Path(f"models/er-qwen35-{args.model}-dpo")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DATA_DIR = Path("data")
TRAIN_FILE = DATA_DIR / "dpo_train.jsonl"
VAL_FILE = DATA_DIR / "dpo_val.jsonl"

if not SFT_ADAPTER.exists():
    print(f"ERROR: SFT adapter not found at {SFT_ADAPTER}. Run sft_train.py first.")
    exit(1)

print(f"=" * 60)
print(f"Endless Rumination — DPO Training (bf16 LoRA)")
print(f"=" * 60)
print(f"SFT adapter:  {SFT_ADAPTER}")
print(f"DPO beta:     {args.beta}")
print(f"LR:           {args.lr}")
print(f"Epochs:       {args.epochs}")
print(f"Batch size:   {args.batch_size} x {args.grad_accum} = {args.batch_size * args.grad_accum} effective")
print(f"Output:       {OUTPUT_DIR}")
print(f"=" * 60)

print("\nLoading libraries...")

# NOTE: We intentionally skip Unsloth for DPO training. Unsloth's patched
# DPOTrainer misidentifies Qwen 3.5 as a vision model (qwen3_5 shares
# model_type with Qwen3.5-VL) and crashes with KeyError: 'images'.
# Vanilla transformers + PEFT + TRL works correctly for DPO.
# SFT was done with Unsloth (for speed), DPO is 1 epoch on small data so
# the ~2x speed penalty is acceptable (~1hr vs ~30min).

import torch

# Prevent Unsloth from patching TRL trainers — we want vanilla DPO
import sys
_unsloth_modules = [k for k in sys.modules if 'unsloth' in k]
_saved_unsloth = {k: sys.modules.pop(k) for k in _unsloth_modules}

from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from datasets import load_dataset
from trl import DPOTrainer, DPOConfig

# Restore unsloth modules (in case anything else needs them)
sys.modules.update(_saved_unsloth)

# Load base model + SFT adapter via vanilla PEFT
print(f"\nLoading SFT adapter from {SFT_ADAPTER} in bf16...")

# Read adapter config to get base model name
adapter_config = json.loads((SFT_ADAPTER / "adapter_config.json").read_text())
base_model_name = adapter_config["base_model_name_or_path"]
print(f"Base model: {base_model_name}")

tokenizer = AutoTokenizer.from_pretrained(str(SFT_ADAPTER))

model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    attn_implementation="eager",  # Flash Attention doesn't work on Blackwell SM_120
)

# Load the SFT LoRA adapter
model = PeftModel.from_pretrained(model, str(SFT_ADAPTER), is_trainable=True)
print(f"Loaded SFT adapter, trainable params: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")

# TRL's DPOTrainer expects a 'warnings_issued' dict on the model (for tracking
# whether certain warnings have been shown). PeftModel doesn't have it, so
# attribute lookup falls through to the base model which also doesn't have it.
if not hasattr(model, "warnings_issued"):
    model.warnings_issued = {}

# Load DPO dataset
print(f"\nLoading DPO data...")

dataset = load_dataset("json", data_files={
    "train": str(TRAIN_FILE),
    "validation": str(VAL_FILE),
})

print(f"DPO train pairs: {len(dataset['train'])}")
print(f"DPO val pairs:   {len(dataset['validation'])}")

# Training
print(f"\nStarting DPO training...")

training_args = DPOConfig(
    output_dir=str(OUTPUT_DIR),
    num_train_epochs=args.epochs,
    per_device_train_batch_size=args.batch_size,
    gradient_accumulation_steps=args.grad_accum,
    learning_rate=args.lr,
    lr_scheduler_type="cosine",
    warmup_ratio=0.1,
    beta=args.beta,
    bf16=True,
    logging_steps=10,
    eval_strategy="epoch",
    save_strategy="epoch",
    save_total_limit=1,
    max_length=2048,
    max_prompt_length=1024,
    seed=42,
    report_to="none",
)

trainer = DPOTrainer(
    model=model,
    processing_class=tokenizer,
    train_dataset=dataset["train"],
    eval_dataset=dataset["validation"],
    args=training_args,
)

trainer.train()

# Save
print(f"\nSaving DPO adapter to {OUTPUT_DIR}...")
model.save_pretrained(str(OUTPUT_DIR))
tokenizer.save_pretrained(str(OUTPUT_DIR))

config = {
    "sft_adapter": str(SFT_ADAPTER),
    "quantization": "bf16 (no QLoRA)",
    "beta": args.beta,
    "lr": args.lr,
    "epochs": args.epochs,
    "batch_size": args.batch_size,
    "grad_accum": args.grad_accum,
    "train_pairs": len(dataset["train"]),
    "val_pairs": len(dataset["validation"]),
}
(OUTPUT_DIR / "training_config.json").write_text(json.dumps(config, indent=2))

print(f"\nDone! DPO adapter saved to {OUTPUT_DIR}")
print(f"Next: Run merge_and_export.py to merge adapters and export.")
