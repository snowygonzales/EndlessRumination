"""Phase 1.6 — Format filtered responses into ChatML training format.

Converts teacher responses and DPO pairs into the format expected by
Qwen3 fine-tuning (ChatML with <|im_start|>/<|im_end|> tokens).

Usage:
    source backend/.venv/bin/activate
    python scripts/distillation/format_training_data.py

Input:  data/filtered_responses.jsonl, data/dpo_pairs.jsonl
Output: data/sft_train.jsonl, data/sft_val.jsonl,
        data/dpo_train.jsonl, data/dpo_val.jsonl
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

SFT_INPUT = DATA_DIR / "filtered_responses.jsonl"
DPO_INPUT = DATA_DIR / "dpo_pairs.jsonl"

SFT_TRAIN = DATA_DIR / "sft_train.jsonl"
SFT_VAL = DATA_DIR / "sft_val.jsonl"
DPO_TRAIN = DATA_DIR / "dpo_train.jsonl"
DPO_VAL = DATA_DIR / "dpo_val.jsonl"

VAL_RATIO = 0.1  # 10% validation
RANDOM_SEED = 42


def format_sft_example(response: dict) -> dict:
    """Convert a teacher response into Qwen3 ChatML SFT format.

    Qwen3 expects conversations in this format:
    [
      {"role": "system", "content": "..."},
      {"role": "user", "content": "..."},
      {"role": "assistant", "content": "..."}
    ]
    """
    # The assistant response is headline + blank line + body
    assistant_content = f"{response['headline']}\n\n{response['body']}"

    return {
        "messages": [
            {"role": "system", "content": response["system_prompt"]},
            {"role": "user", "content": response["problem"]},
            {"role": "assistant", "content": assistant_content},
        ]
    }


def format_dpo_example(pair: dict) -> dict:
    """Convert a DPO pair into the format expected by TRL's DPOTrainer.

    TRL DPOTrainer expects:
    {
      "prompt": [system + user messages],
      "chosen": "good response text",
      "rejected": "bad response text"
    }
    """
    return {
        "prompt": [
            {"role": "system", "content": pair["system_prompt"]},
            {"role": "user", "content": pair["problem"]},
        ],
        "chosen": [
            {"role": "assistant", "content": pair["chosen"]},
        ],
        "rejected": [
            {"role": "assistant", "content": pair["rejected"]},
        ],
    }


def split_train_val(data: list, val_ratio: float, seed: int) -> tuple[list, list]:
    """Split data into train/val sets, stratified by lens_index if possible."""
    random.seed(seed)
    shuffled = data.copy()
    random.shuffle(shuffled)
    split_idx = int(len(shuffled) * (1 - val_ratio))
    return shuffled[:split_idx], shuffled[split_idx:]


def write_jsonl(path: Path, data: list):
    """Write list of dicts to JSONL file."""
    with open(path, "w") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def main():
    # ── SFT Data ──
    if SFT_INPUT.exists():
        responses = []
        with open(SFT_INPUT) as f:
            for line in f:
                if line.strip():
                    responses.append(json.loads(line))

        print(f"Loaded {len(responses)} filtered responses for SFT")

        sft_examples = [format_sft_example(r) for r in responses]
        sft_train, sft_val = split_train_val(sft_examples, VAL_RATIO, RANDOM_SEED)

        write_jsonl(SFT_TRAIN, sft_train)
        write_jsonl(SFT_VAL, sft_val)

        print(f"  SFT train: {len(sft_train)} → {SFT_TRAIN}")
        print(f"  SFT val:   {len(sft_val)} → {SFT_VAL}")

        # Validate a sample
        sample = sft_train[0]
        msgs = sample["messages"]
        print(f"\n  Sample SFT example:")
        print(f"    System prompt length: {len(msgs[0]['content'])} chars")
        print(f"    User problem length:  {len(msgs[1]['content'])} chars")
        print(f"    Assistant response:    {len(msgs[2]['content'])} chars")
        print(f"    First 100 chars:      {msgs[2]['content'][:100]}...")
    else:
        print(f"WARNING: {SFT_INPUT} not found, skipping SFT formatting")

    # ── DPO Data ──
    if DPO_INPUT.exists():
        pairs = []
        with open(DPO_INPUT) as f:
            for line in f:
                if line.strip():
                    pairs.append(json.loads(line))

        print(f"\nLoaded {len(pairs)} DPO pairs")

        dpo_examples = [format_dpo_example(p) for p in pairs]
        dpo_train, dpo_val = split_train_val(dpo_examples, VAL_RATIO, RANDOM_SEED)

        write_jsonl(DPO_TRAIN, dpo_train)
        write_jsonl(DPO_VAL, dpo_val)

        print(f"  DPO train: {len(dpo_train)} → {DPO_TRAIN}")
        print(f"  DPO val:   {len(dpo_val)} → {DPO_VAL}")
    else:
        print(f"WARNING: {DPO_INPUT} not found, skipping DPO formatting")

    # ── Summary ──
    print("\n" + "=" * 50)
    print("Training data ready! Files:")
    for path in [SFT_TRAIN, SFT_VAL, DPO_TRAIN, DPO_VAL]:
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            with open(path) as f:
                count = sum(1 for _ in f)
            print(f"  {path.name}: {count} examples ({size_mb:.1f} MB)")
    print("=" * 50)
    print("\nNext: Transfer these files to your RTX 5090 PC and run training scripts.")


if __name__ == "__main__":
    main()
