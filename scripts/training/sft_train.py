"""Phase 2.1/2.2 — QLoRA SFT fine-tuning using Unsloth.

Trains a Qwen3 model on the distilled dataset using QLoRA
(Quantized Low-Rank Adaptation) for efficient fine-tuning.

Run this on the RTX 5090 PC (32GB VRAM).

Usage:
    pip install unsloth torch transformers datasets trl accelerate bitsandbytes
    python scripts/training/sft_train.py --model 4b    # Qwen3-4B
    python scripts/training/sft_train.py --model 1.7b  # Qwen3-1.7B

Input:  data/sft_train.jsonl, data/sft_val.jsonl
Output: models/er-qwen3-{size}-sft/
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

# ── Parse args before heavy imports ──
parser = argparse.ArgumentParser(description="QLoRA SFT training for Endless Rumination")
parser.add_argument(
    "--model",
    choices=["4b", "1.7b"],
    default="4b",
    help="Model size to fine-tune (default: 4b)",
)
parser.add_argument("--epochs", type=int, default=None, help="Override epoch count")
parser.add_argument("--batch-size", type=int, default=4, help="Per-device batch size")
parser.add_argument("--grad-accum", type=int, default=4, help="Gradient accumulation steps")
parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
parser.add_argument("--max-seq-len", type=int, default=2048, help="Max sequence length")
parser.add_argument("--lora-rank", type=int, default=32, help="LoRA rank")
parser.add_argument("--resume", action="store_true", help="Resume from last checkpoint")

args = parser.parse_args()

# ── Config ──
MODEL_MAP = {
    "4b": "Qwen/Qwen3-4B-Instruct",
    "1.7b": "Qwen/Qwen3-1.7B-Instruct",
}
DEFAULT_EPOCHS = {"4b": 3, "1.7b": 5}

BASE_MODEL = MODEL_MAP[args.model]
NUM_EPOCHS = args.epochs or DEFAULT_EPOCHS[args.model]
OUTPUT_DIR = Path(f"models/er-qwen3-{args.model}-sft")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DATA_DIR = Path("data")
TRAIN_FILE = DATA_DIR / "sft_train.jsonl"
VAL_FILE = DATA_DIR / "sft_val.jsonl"

print(f"=" * 60)
print(f"Endless Rumination — QLoRA SFT Training")
print(f"=" * 60)
print(f"Base model:  {BASE_MODEL}")
print(f"LoRA rank:   {args.lora_rank}")
print(f"Epochs:      {NUM_EPOCHS}")
print(f"Batch size:  {args.batch_size} x {args.grad_accum} = {args.batch_size * args.grad_accum} effective")
print(f"Max seq len: {args.max_seq_len}")
print(f"LR:          {args.lr}")
print(f"Output:      {OUTPUT_DIR}")
print(f"=" * 60)

# ── Heavy imports ──
print("\nLoading libraries...")

from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig

# ── Load model with QLoRA ──
print(f"\nLoading {BASE_MODEL} with 4-bit quantization...")

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=BASE_MODEL,
    max_seq_length=args.max_seq_len,
    load_in_4bit=True,
    dtype=None,  # auto-detect
)

# Apply LoRA adapters
model = FastLanguageModel.get_peft_model(
    model,
    r=args.lora_rank,
    lora_alpha=args.lora_rank * 2,  # alpha = 2 * rank is standard
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",  # memory optimization
    random_state=42,
)

print(f"Trainable parameters: {model.print_trainable_parameters()}")

# ── Load dataset ──
print(f"\nLoading training data from {TRAIN_FILE}...")

dataset = load_dataset("json", data_files={
    "train": str(TRAIN_FILE),
    "validation": str(VAL_FILE),
})

print(f"Train examples: {len(dataset['train'])}")
print(f"Val examples:   {len(dataset['validation'])}")


def format_chat(example):
    """Apply chat template to messages."""
    text = tokenizer.apply_chat_template(
        example["messages"],
        tokenize=False,
        add_generation_prompt=False,
    )
    return {"text": text}


dataset = dataset.map(format_chat)

# ── Training ──
print(f"\nStarting training...")

training_args = SFTConfig(
    output_dir=str(OUTPUT_DIR),
    num_train_epochs=NUM_EPOCHS,
    per_device_train_batch_size=args.batch_size,
    gradient_accumulation_steps=args.grad_accum,
    learning_rate=args.lr,
    lr_scheduler_type="cosine",
    warmup_ratio=0.05,
    weight_decay=0.01,
    bf16=True,
    logging_steps=10,
    eval_strategy="epoch",
    save_strategy="epoch",
    save_total_limit=2,
    load_best_model_at_end=True,
    metric_for_best_model="eval_loss",
    greater_is_better=False,
    max_seq_length=args.max_seq_len,
    dataset_text_field="text",
    packing=True,  # Unsloth packing for efficiency
    seed=42,
    report_to="none",  # disable wandb/tensorboard
)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset["train"],
    eval_dataset=dataset["validation"],
    args=training_args,
)

if args.resume:
    trainer.train(resume_from_checkpoint=True)
else:
    trainer.train()

# ── Save ──
print(f"\nSaving LoRA adapter to {OUTPUT_DIR}...")
model.save_pretrained(str(OUTPUT_DIR))
tokenizer.save_pretrained(str(OUTPUT_DIR))

# Also save training config for reproducibility
config = {
    "base_model": BASE_MODEL,
    "lora_rank": args.lora_rank,
    "lora_alpha": args.lora_rank * 2,
    "epochs": NUM_EPOCHS,
    "batch_size": args.batch_size,
    "grad_accum": args.grad_accum,
    "lr": args.lr,
    "max_seq_len": args.max_seq_len,
    "train_examples": len(dataset["train"]),
    "val_examples": len(dataset["validation"]),
}
(OUTPUT_DIR / "training_config.json").write_text(json.dumps(config, indent=2))

print(f"\nDone! SFT adapter saved to {OUTPUT_DIR}")
print(f"Next: Run dpo_train.py to further align with preferences.")
