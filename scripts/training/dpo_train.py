"""Phase 2.3 — DPO training on top of SFT adapter.

Direct Preference Optimization teaches the model what "good" looks like
relative to "bad" — better than SFT alone for style/quality alignment.

Run this on the RTX 5090 PC (32GB VRAM).

Usage:
    python scripts/training/dpo_train.py --model 4b
    python scripts/training/dpo_train.py --model 1.7b

Input:  data/dpo_train.jsonl, data/dpo_val.jsonl,
        models/er-qwen3-{size}-sft/ (SFT adapter)
Output: models/er-qwen3-{size}-dpo/
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description="DPO training for Endless Rumination")
parser.add_argument("--model", choices=["4b", "1.7b"], default="4b")
parser.add_argument("--beta", type=float, default=0.1, help="DPO beta parameter")
parser.add_argument("--lr", type=float, default=5e-5, help="Learning rate")
parser.add_argument("--epochs", type=int, default=1, help="DPO epochs")
parser.add_argument("--batch-size", type=int, default=2, help="Per-device batch size")
parser.add_argument("--grad-accum", type=int, default=4, help="Gradient accumulation")

args = parser.parse_args()

MODEL_MAP = {
    "4b": "Qwen/Qwen3-4B-Instruct",
    "1.7b": "Qwen/Qwen3-1.7B-Instruct",
}

BASE_MODEL = MODEL_MAP[args.model]
SFT_ADAPTER = Path(f"models/er-qwen3-{args.model}-sft")
OUTPUT_DIR = Path(f"models/er-qwen3-{args.model}-dpo")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DATA_DIR = Path("data")
TRAIN_FILE = DATA_DIR / "dpo_train.jsonl"
VAL_FILE = DATA_DIR / "dpo_val.jsonl"

if not SFT_ADAPTER.exists():
    print(f"ERROR: SFT adapter not found at {SFT_ADAPTER}. Run sft_train.py first.")
    exit(1)

print(f"=" * 60)
print(f"Endless Rumination — DPO Training")
print(f"=" * 60)
print(f"Base model:   {BASE_MODEL}")
print(f"SFT adapter:  {SFT_ADAPTER}")
print(f"DPO beta:     {args.beta}")
print(f"LR:           {args.lr}")
print(f"Epochs:       {args.epochs}")
print(f"Output:       {OUTPUT_DIR}")
print(f"=" * 60)

print("\nLoading libraries...")

from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import DPOTrainer, DPOConfig

# Load model with SFT adapter
print(f"\nLoading {BASE_MODEL} + SFT adapter...")

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=str(SFT_ADAPTER),
    max_seq_length=2048,
    load_in_4bit=True,
    dtype=None,
)

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
    tokenizer=tokenizer,
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
    "base_model": BASE_MODEL,
    "sft_adapter": str(SFT_ADAPTER),
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
