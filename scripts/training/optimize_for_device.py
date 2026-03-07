"""Step 4.5 — Optimize merged model for on-device deployment.

Strips unnecessary components from the merged Qwen 3.5 model to minimize
memory footprint for 6GB iOS devices:
  1. Remove vision encoder weights (667 MB in bf16, ~167 MB at 4-bit)
  2. Optionally prune vocabulary to English-only tokens (~154 MB at 4-bit)

Usage:
    source ~/er-train-venv/bin/activate
    python scripts/training/optimize_for_device.py --model 4b
    python scripts/training/optimize_for_device.py --model 4b --prune-vocab

Input:  models/er-qwen35-{size}-merged/
Output: models/er-qwen35-{size}-optimized/
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

parser = argparse.ArgumentParser(description="Optimize model for on-device deployment")
parser.add_argument("--model", choices=["4b", "2b"], default="4b")
parser.add_argument("--prune-vocab", action="store_true",
                    help="Prune non-English tokens from vocabulary (saves ~154 MB at 4-bit)")
parser.add_argument("--vocab-keep-ids", type=str, default=None,
                    help="Path to JSON file with token IDs to keep (auto-generated if not provided)")

args = parser.parse_args()

MERGED_DIR = Path(f"models/er-qwen35-{args.model}-merged")
OUTPUT_DIR = Path(f"models/er-qwen35-{args.model}-optimized")

if not MERGED_DIR.exists():
    print(f"ERROR: Merged model not found at {MERGED_DIR}")
    exit(1)

print("=" * 60)
print("Optimizing model for on-device deployment")
print(f"  Input:  {MERGED_DIR}")
print(f"  Output: {OUTPUT_DIR}")
print(f"  Strip vision: YES")
print(f"  Prune vocab:  {'YES' if args.prune_vocab else 'NO'}")
print("=" * 60)

# ── Step 0: Load libraries ──

print("\nLoading libraries...")
import torch
from safetensors.torch import load_file, save_file

# ── Step 1: Strip vision encoder ──

print("\n── Step 1: Stripping vision encoder weights ──")

safetensor_files = sorted(f for f in MERGED_DIR.glob("*.safetensors") if f.suffix == ".safetensors")

print(f"Found {len(safetensor_files)} safetensor file(s)")

# Load all tensors, filtering out vision
all_tensors = {}
vision_params = 0
vision_bytes = 0
kept_params = 0
kept_bytes = 0

for f in safetensor_files:
    print(f"  Loading {f.name}...")
    tensors = load_file(str(f), device="cpu")
    for key, tensor in tensors.items():
        size = tensor.numel()
        byte_size = size * tensor.element_size()
        if "visual" in key or "vision" in key:
            vision_params += size
            vision_bytes += byte_size
        else:
            all_tensors[key] = tensor
            kept_params += size
            kept_bytes += byte_size

print(f"\n  Stripped {vision_params:,} vision params ({vision_bytes / 1e6:.0f} MB)")
print(f"  Kept {kept_params:,} text params ({kept_bytes / 1e6:.0f} MB)")

# ── Step 2: Vocabulary pruning (optional) ──

keep_ids = None

if args.prune_vocab:
    print("\n── Step 2: Pruning vocabulary ──")

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(str(MERGED_DIR))

    if args.vocab_keep_ids:
        # Use provided keep list
        with open(args.vocab_keep_ids) as f:
            keep_ids = sorted(json.load(f))
        print(f"  Loaded {len(keep_ids)} token IDs to keep from {args.vocab_keep_ids}")
    else:
        # Auto-detect: keep ASCII + tokens found in training data
        print("  Auto-detecting tokens to keep...")

        keep_ids_set = set()

        # 1. Keep all ASCII-range tokens and common subwords
        print("    Scanning vocabulary for ASCII tokens...")
        for i in range(len(tokenizer)):
            try:
                decoded = tokenizer.decode([i])
                # Keep if all chars are ASCII/Latin or common punctuation
                if all(ord(c) < 0x0370 for c in decoded):  # Latin + Latin Extended
                    keep_ids_set.add(i)
            except Exception:
                keep_ids_set.add(i)  # keep if we can't decode (special tokens)

        # 2. Keep all special tokens
        for attr in ["bos_token_id", "eos_token_id", "pad_token_id", "unk_token_id"]:
            tid = getattr(tokenizer, attr, None)
            if tid is not None:
                keep_ids_set.add(tid)
        if hasattr(tokenizer, "additional_special_tokens_ids"):
            keep_ids_set.update(tokenizer.additional_special_tokens_ids)

        # 3. Scan training data for any additional tokens used
        data_files = list(Path("data").glob("*.jsonl"))
        if data_files:
            print(f"    Scanning {len(data_files)} data files for used tokens...")
            for df in data_files:
                with open(df) as fh:
                    for line in fh:
                        try:
                            row = json.loads(line)
                            # Tokenize all text fields
                            for field in ["text", "prompt", "chosen", "rejected"]:
                                if field in row:
                                    text = row[field] if isinstance(row[field], str) else json.dumps(row[field])
                                    ids = tokenizer.encode(text, add_special_tokens=False)
                                    keep_ids_set.update(ids)
                        except (json.JSONDecodeError, Exception):
                            continue
        else:
            print("    No data/ files found — keeping only ASCII tokens")

        # 4. Safety margin: keep top-frequency tokens up to 32K minimum
        min_vocab = 32_000
        if len(keep_ids_set) < min_vocab:
            # Pad with sequential IDs (low IDs tend to be common tokens)
            for i in range(min_vocab):
                keep_ids_set.add(i)

        keep_ids = sorted(keep_ids_set)
        print(f"    Keeping {len(keep_ids)} / {len(tokenizer)} tokens ({100*len(keep_ids)/len(tokenizer):.1f}%)")

        # Save keep list for reproducibility
        keep_list_path = MERGED_DIR / "vocab_keep_ids.json"
        with open(keep_list_path, "w") as f:
            json.dump(keep_ids, f)
        print(f"    Saved keep list to {keep_list_path}")

    # Now prune the embedding tensor
    orig_vocab = None
    new_vocab = len(keep_ids)
    keep_tensor = torch.tensor(keep_ids, dtype=torch.long)

    for key in list(all_tensors.keys()):
        if "embed_tokens.weight" in key:
            orig = all_tensors[key]
            orig_vocab = orig.shape[0]
            pruned = orig[keep_tensor]
            saved = (orig.numel() - pruned.numel()) * orig.element_size()
            all_tensors[key] = pruned
            print(f"  embed_tokens: {list(orig.shape)} → {list(pruned.shape)} (saved {saved/1e6:.0f} MB)")

        elif "lm_head.weight" in key:
            orig = all_tensors[key]
            pruned = orig[keep_tensor]
            saved = (orig.numel() - pruned.numel()) * orig.element_size()
            all_tensors[key] = pruned
            print(f"  lm_head: {list(orig.shape)} → {list(pruned.shape)} (saved {saved/1e6:.0f} MB)")

    if orig_vocab:
        print(f"\n  Vocabulary: {orig_vocab:,} → {new_vocab:,} ({100*new_vocab/orig_vocab:.1f}%)")

# ── Step 3: Save optimized model ──

print("\n── Step 3: Saving optimized model ──")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Save tensors as single safetensors file (should fit in memory for 4B)
total_bytes = sum(t.numel() * t.element_size() for t in all_tensors.values())
print(f"  Total size: {total_bytes / 1e9:.2f} GB")

out_path = OUTPUT_DIR / "model.safetensors"
print(f"  Saving to {out_path}...")
save_file(all_tensors, str(out_path))

# Copy and update config
print("  Updating config.json...")
with open(MERGED_DIR / "config.json") as f:
    config = json.load(f)

# Remove vision config
for key in ["vision_config", "visual"]:
    config.pop(key, None)

# If we have a text_config nested, promote it
if "text_config" in config:
    text_config = config.pop("text_config")
    # Merge text_config fields into top level, keeping existing top-level fields
    for k, v in text_config.items():
        if k not in config:
            config[k] = v

# Update model_type to text-only
if config.get("model_type") == "qwen3_5":
    config["model_type"] = "qwen3_5_text"

# Update vocab size if pruned
if keep_ids is not None:
    config["vocab_size"] = len(keep_ids)

with open(OUTPUT_DIR / "config.json", "w") as f:
    json.dump(config, f, indent=2)

# Copy tokenizer files
print("  Copying tokenizer files...")
tokenizer_files = [
    "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json",
    "vocab.json", "merges.txt",  # BPE tokenizer files
]
for tf in tokenizer_files:
    src = MERGED_DIR / tf
    if src.exists():
        shutil.copy2(src, OUTPUT_DIR / tf)

# If vocab was pruned, we need to update the tokenizer
if keep_ids is not None:
    print("  Updating tokenizer for pruned vocabulary...")
    # Create ID mapping: old_id -> new_id
    id_map = {old_id: new_id for new_id, old_id in enumerate(keep_ids)}

    # Update tokenizer.json if it exists (fast tokenizer)
    tok_json_path = OUTPUT_DIR / "tokenizer.json"
    if tok_json_path.exists():
        with open(tok_json_path) as f:
            tok_data = json.load(f)

        # Update the vocab in the model section
        if "model" in tok_data and "vocab" in tok_data["model"]:
            old_vocab = tok_data["model"]["vocab"]
            new_vocab_dict = {}
            for token, old_id in old_vocab.items():
                if old_id in id_map:
                    new_vocab_dict[token] = id_map[old_id]
            tok_data["model"]["vocab"] = new_vocab_dict

        # Update added_tokens
        if "added_tokens" in tok_data:
            new_added = []
            for at in tok_data["added_tokens"]:
                if at["id"] in id_map:
                    at["id"] = id_map[at["id"]]
                    new_added.append(at)
            tok_data["added_tokens"] = new_added

        with open(tok_json_path, "w") as f:
            json.dump(tok_data, f, indent=2)

    # Update tokenizer_config.json
    tok_config_path = OUTPUT_DIR / "tokenizer_config.json"
    if tok_config_path.exists():
        with open(tok_config_path) as f:
            tok_config = json.load(f)
        # Update special token IDs
        for key in ["bos_token_id", "eos_token_id", "pad_token_id"]:
            if key in tok_config and tok_config[key] in id_map:
                tok_config[key] = id_map[tok_config[key]]
        with open(tok_config_path, "w") as f:
            json.dump(tok_config, f, indent=2)

# Copy safetensors index if needed (we're saving single file, so create new index)
index = {
    "metadata": {"total_size": total_bytes},
    "weight_map": {k: "model.safetensors" for k in all_tensors.keys()},
}
with open(OUTPUT_DIR / "model.safetensors.index.json", "w") as f:
    json.dump(index, f, indent=2)

# Copy generation_config if exists
gen_config_src = MERGED_DIR / "generation_config.json"
if gen_config_src.exists():
    shutil.copy2(gen_config_src, OUTPUT_DIR / "generation_config.json")

# ── Summary ──

orig_size = sum(f.stat().st_size for f in MERGED_DIR.glob("*.safetensors"))
opt_size = out_path.stat().st_size

print(f"\n{'=' * 60}")
print(f"Optimization complete!")
print(f"  Original: {orig_size / 1e9:.2f} GB ({MERGED_DIR})")
print(f"  Optimized: {opt_size / 1e9:.2f} GB ({OUTPUT_DIR})")
print(f"  Saved: {(orig_size - opt_size) / 1e6:.0f} MB ({100*(1 - opt_size/orig_size):.1f}%)")
print(f"\n  4-bit estimate: ~{opt_size / 4 / 1e9:.2f} GB")
if keep_ids:
    print(f"  Vocab: {orig_vocab:,} → {len(keep_ids):,}")
print(f"\nNext step (on Mac):")
print(f"  python -m mlx_lm.convert --model {OUTPUT_DIR} --quantize --q-bits 4 --q-group-size 64 -o models/er-qwen35-{args.model}-mlx-4bit")
print(f"{'=' * 60}")
