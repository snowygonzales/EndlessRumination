#!/usr/bin/env python3
"""Batch-generate takes from the fine-tuned model for quality review.

Reads prompts from data/expanded_prompts.jsonl, generates takes through all 40
lenses using the on-device MLX model, and outputs:
  - data/batch_takes/takes.jsonl  (machine-readable, one take per line)
  - data/batch_takes/report.html  (human-readable browsable report)

Usage (from project root, inside .mlx-venv):
  python scripts/evaluation/batch_generate.py                     # 10 problems x 40 lenses
  python scripts/evaluation/batch_generate.py --problems 200      # 200 problems x 40 lenses
  python scripts/evaluation/batch_generate.py --problems 5 --lenses 0-4   # 5 problems x 5 base lenses
  python scripts/evaluation/batch_generate.py --resume            # resume from last checkpoint

Time estimates (Mac Mini M1, 4B model @ ~20 tok/s):
  10 problems x 40 lenses  =   400 takes  ~  67 minutes
  50 problems x 40 lenses  = 2,000 takes  ~ 5.5 hours
 200 problems x 40 lenses  = 8,000 takes  ~  22 hours
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import timedelta
from pathlib import Path

# ── Resolve project root ────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Add backend to path so we can import lens definitions directly
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.lenses.definitions import LENSES, FORMAT_INSTRUCTION
from app.lenses.voice_packs import VOICE_PACKS


# ── Build flat lens lookup ──────────────────────────────────────────────────

def build_lens_map() -> dict[int, dict]:
    """Build a flat map of lens index -> {name, emoji, system_prompt}."""
    lenses = {}
    for lens in LENSES:
        lenses[lens["index"]] = {
            "name": lens["name"],
            "emoji": lens["emoji"],
            "system_prompt": lens["system_prompt"],
        }
    for pack in VOICE_PACKS:
        for voice in pack["voices"]:
            lenses[voice["index"]] = {
                "name": voice["name"],
                "emoji": voice["emoji"],
                "system_prompt": voice["system_prompt"],
                "pack": pack["name"],
            }
    return lenses


ALL_LENSES = build_lens_map()


# ── Parse lens range ────────────────────────────────────────────────────────

def parse_lens_range(spec: str) -> list[int]:
    """Parse a lens specification like '0-19', '0-4,20-24', 'all'."""
    if spec.lower() == "all":
        return sorted(ALL_LENSES.keys())
    indices = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            indices.update(range(int(lo), int(hi) + 1))
        else:
            indices.add(int(part))
    valid = sorted(i for i in indices if i in ALL_LENSES)
    if not valid:
        print(f"ERROR: No valid lens indices in '{spec}'. Valid: 0-39.")
        sys.exit(1)
    return valid


# ── Load prompts ────────────────────────────────────────────────────────────

def load_prompts(path: Path, count: int) -> list[dict]:
    """Load N prompts from expanded_prompts.jsonl."""
    prompts = []
    with open(path) as f:
        for line in f:
            if len(prompts) >= count:
                break
            prompts.append(json.loads(line))
    if len(prompts) < count:
        print(f"WARNING: Only {len(prompts)} prompts available (requested {count}).")
    return prompts


# ── Output helpers ──────────────────────────────────────────────────────────

def load_checkpoint(jsonl_path: Path) -> set[str]:
    """Load already-generated (problem_idx, lens_idx) pairs from existing output."""
    done = set()
    if jsonl_path.exists():
        with open(jsonl_path) as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    key = f"{obj['problem_index']}:{obj['lens_index']}"
                    done.add(key)
                except (json.JSONDecodeError, KeyError):
                    continue
    return done


def generate_html(jsonl_path: Path, html_path: Path, prompts: list[dict], lens_indices: list[int]):
    """Generate a browsable HTML report from the JSONL output."""
    # Load all takes
    takes_by_problem: dict[int, dict[int, dict]] = {}
    with open(jsonl_path) as f:
        for line in f:
            obj = json.loads(line)
            pid = obj["problem_index"]
            lid = obj["lens_index"]
            if pid not in takes_by_problem:
                takes_by_problem[pid] = {}
            takes_by_problem[pid][lid] = obj

    total_takes = sum(len(v) for v in takes_by_problem.values())
    total_problems = len(takes_by_problem)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Endless Rumination — Batch Takes Review</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #0d0d12; color: #e0dcd4; line-height: 1.6;
    padding: 24px; max-width: 1200px; margin: 0 auto;
  }}
  h1 {{ color: #f0ece4; margin-bottom: 8px; font-size: 28px; }}
  .stats {{ color: #8a8690; margin-bottom: 32px; font-size: 14px; }}
  .problem-card {{
    background: #1a1a22; border-radius: 16px; padding: 24px;
    margin-bottom: 24px; border: 1px solid #2a2a34;
  }}
  .problem-text {{
    color: #f0ece4; font-size: 15px; padding: 16px; margin-bottom: 16px;
    background: #12121a; border-radius: 8px; border-left: 3px solid #e8a54b;
  }}
  .problem-meta {{
    color: #6a6670; font-size: 12px; margin-bottom: 12px;
  }}
  .takes-grid {{
    display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 12px;
  }}
  .take {{
    background: #12121a; border-radius: 12px; padding: 16px;
    border: 1px solid #2a2a34; transition: border-color 0.2s;
  }}
  .take:hover {{ border-color: #e8a54b; }}
  .take-lens {{
    font-size: 12px; color: #8a8690; margin-bottom: 8px;
    display: flex; align-items: center; gap: 6px;
  }}
  .take-headline {{
    font-size: 15px; font-weight: 600; color: #f0ece4; margin-bottom: 8px;
  }}
  .take-body {{
    font-size: 13px; color: #b0acaa; line-height: 1.7;
  }}
  .take-meta {{
    font-size: 11px; color: #4a4650; margin-top: 8px;
  }}
  .take-error {{
    color: #ff4757; font-size: 12px; font-style: italic;
  }}
  .toc {{ margin-bottom: 32px; }}
  .toc a {{ color: #e8a54b; text-decoration: none; font-size: 13px; }}
  .toc a:hover {{ text-decoration: underline; }}
  .nav {{ position: fixed; bottom: 24px; right: 24px; }}
  .nav a {{
    display: block; background: #e8a54b; color: #0d0d12; padding: 8px 16px;
    border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 600;
  }}
  .collapse-btn {{
    background: none; border: 1px solid #3a3a44; color: #8a8690;
    padding: 4px 12px; border-radius: 6px; cursor: pointer; font-size: 12px;
    margin-bottom: 12px;
  }}
  .collapse-btn:hover {{ border-color: #e8a54b; color: #e8a54b; }}
</style>
</head>
<body>
<h1>Batch Takes Review</h1>
<p class="stats">{total_takes} takes across {total_problems} problems &bull;
   {len(lens_indices)} lenses &bull; Model: er-qwen35-4b-mlx-4bit</p>

<div class="toc">
<strong style="color:#8a8690;font-size:13px;">Jump to problem:</strong><br>
"""
    # Table of contents
    for pid in sorted(takes_by_problem.keys()):
        if pid < len(prompts):
            short = prompts[pid]["problem"][:80] + ("..." if len(prompts[pid]["problem"]) > 80 else "")
            html += f'<a href="#p{pid}">#{pid}: {_html_escape(short)}</a><br>\n'

    html += "</div>\n"

    # Problem cards
    for pid in sorted(takes_by_problem.keys()):
        if pid >= len(prompts):
            continue
        prompt = prompts[pid]
        html += f"""
<div class="problem-card" id="p{pid}">
  <div class="problem-meta">Problem #{pid} &bull; {_html_escape(prompt.get('category', '?'))} &bull; complexity {prompt.get('complexity', '?')}</div>
  <div class="problem-text">{_html_escape(prompt['problem'])}</div>
  <button class="collapse-btn" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'grid' : 'none'">Toggle takes</button>
  <div class="takes-grid">
"""
        for lid in lens_indices:
            lens_info = ALL_LENSES[lid]
            take = takes_by_problem[pid].get(lid)
            if take and take.get("headline"):
                html += f"""    <div class="take">
      <div class="take-lens">{lens_info['emoji']} {_html_escape(lens_info['name'])} <span style="color:#4a4650">#{lid}</span></div>
      <div class="take-headline">{_html_escape(take['headline'])}</div>
      <div class="take-body">{_html_escape(take['body'])}</div>
      <div class="take-meta">{take.get('tokens_per_sec', '?'):.1f} tok/s &bull; {take.get('generation_time_s', '?'):.1f}s</div>
    </div>
"""
            elif take:
                html += f"""    <div class="take">
      <div class="take-lens">{lens_info['emoji']} {_html_escape(lens_info['name'])} <span style="color:#4a4650">#{lid}</span></div>
      <div class="take-error">{_html_escape(take.get('error', 'Parse failed'))}</div>
    </div>
"""
        html += "  </div>\n</div>\n"

    html += """
<div class="nav"><a href="#top">&#8593; Top</a></div>
</body></html>"""

    with open(html_path, "w") as f:
        f.write(html)


def _html_escape(text: str) -> str:
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("\n", "<br>"))


# ── Pre-canned headlines (matches iOS LocalTakeGenerator) ───────────────────

CANNED_HEADLINES = [
    "A Fresh Perspective",
    "A New Take",
    "Here's Another Look",
    "Consider This",
    "A Different Angle",
    "Something to Think About",
    "One More Way to See It",
    "Flip the Script",
]


def parse_take(raw: str, lens_index: int) -> tuple[str, str] | None:
    """Use entire model output as body with a pre-canned headline."""
    cleaned = raw.strip()
    if not cleaned:
        return None
    headline = CANNED_HEADLINES[lens_index % len(CANNED_HEADLINES)]
    return headline, cleaned


# ── Main generation loop ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Batch-generate takes for quality review")
    parser.add_argument("--problems", type=int, default=10,
                        help="Number of problems to process (default: 10)")
    parser.add_argument("--lenses", type=str, default="all",
                        help="Lens indices: 'all', '0-19', '0-4,20-24' (default: all)")
    parser.add_argument("--model", type=str, default="sefiroth/er-qwen35-4b-mlx-4bit",
                        help="HuggingFace model ID or local path")
    parser.add_argument("--max-tokens", type=int, default=200,
                        help="Max tokens per generation (default: 200)")
    parser.add_argument("--temperature", type=float, default=0.7,
                        help="Sampling temperature (default: 0.7)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from existing checkpoint")
    parser.add_argument("--html-only", action="store_true",
                        help="Only regenerate HTML from existing JSONL (no inference)")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Output directory (default: data/batch_takes/)")
    args = parser.parse_args()

    # Paths
    prompts_path = PROJECT_ROOT / "data" / "expanded_prompts.jsonl"
    out_dir = Path(args.output_dir) if args.output_dir else PROJECT_ROOT / "data" / "batch_takes"
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "takes.jsonl"
    html_path = out_dir / "report.html"

    # Parse lens range
    lens_indices = parse_lens_range(args.lenses)
    lens_names = [f"{ALL_LENSES[i]['emoji']} {ALL_LENSES[i]['name']}" for i in lens_indices]

    # Load prompts
    prompts = load_prompts(prompts_path, args.problems)
    total_takes = len(prompts) * len(lens_indices)

    print(f"\n{'='*60}")
    print(f"  Endless Rumination — Batch Generation")
    print(f"{'='*60}")
    print(f"  Problems:  {len(prompts)}")
    print(f"  Lenses:    {len(lens_indices)} ({lens_indices[0]}-{lens_indices[-1]})")
    print(f"  Total:     {total_takes} takes")
    print(f"  Model:     {args.model}")
    print(f"  Temp:      {args.temperature}")
    print(f"  Output:    {out_dir}")
    print(f"{'='*60}\n")

    if args.html_only:
        if jsonl_path.exists():
            print("Regenerating HTML from existing JSONL...")
            generate_html(jsonl_path, html_path, prompts, lens_indices)
            print(f"Done! Open: {html_path}")
        else:
            print(f"ERROR: No JSONL found at {jsonl_path}")
        return

    # Check for resume
    done_keys = set()
    if args.resume and jsonl_path.exists():
        done_keys = load_checkpoint(jsonl_path)
        print(f"Resuming: {len(done_keys)} takes already done, {total_takes - len(done_keys)} remaining.\n")
    elif not args.resume and jsonl_path.exists():
        print(f"WARNING: {jsonl_path} exists. Use --resume to continue or delete it to start fresh.")
        resp = input("Overwrite? [y/N] ").strip().lower()
        if resp != "y":
            print("Aborted.")
            return
        jsonl_path.unlink()

    # ── Load model ──────────────────────────────────────────────────────────
    print("Loading model (this may download ~2GB on first run)...")
    t0 = time.time()

    from mlx_lm import load, generate
    from mlx_lm.sample_utils import make_sampler

    model, tokenizer = load(args.model)
    sampler = make_sampler(temp=args.temperature)

    print(f"Model loaded in {time.time() - t0:.1f}s\n")

    # Stop sequences (same as iOS InferenceEngine)
    stop_sequences = ["<|im_end|>", "<|endoftext|>", "<|im_start|>", "<think>"]

    def clean_output(raw: str) -> str:
        text = raw
        for stop in stop_sequences:
            idx = text.find(stop)
            if idx != -1:
                text = text[:idx]
        return text.strip()

    # ── Generation loop ─────────────────────────────────────────────────────
    completed = len(done_keys)
    errors = 0
    start_time = time.time()

    with open(jsonl_path, "a") as out_f:
        for pi, prompt_obj in enumerate(prompts):
            problem = prompt_obj["problem"]

            for li, lens_idx in enumerate(lens_indices):
                key = f"{pi}:{lens_idx}"
                if key in done_keys:
                    continue

                lens = ALL_LENSES[lens_idx]
                overall_idx = pi * len(lens_indices) + li + 1

                # Build chat messages
                messages = [
                    {"role": "system", "content": lens["system_prompt"]},
                    {"role": "user", "content": problem},
                ]

                # Apply chat template
                prompt_text = tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                    enable_thinking=False,
                )

                # Generate
                gen_start = time.time()
                try:
                    raw = generate(
                        model, tokenizer,
                        prompt=prompt_text,
                        max_tokens=args.max_tokens,
                        sampler=sampler,
                        verbose=False,
                    )
                    gen_time = time.time() - gen_start

                    cleaned = clean_output(raw)
                    parsed = parse_take(cleaned, lens_idx)

                    record = {
                        "problem_index": pi,
                        "problem": problem,
                        "category": prompt_obj.get("category", ""),
                        "lens_index": lens_idx,
                        "lens_name": lens["name"],
                        "raw_output": cleaned,
                        "headline": parsed[0] if parsed else None,
                        "body": parsed[1] if parsed else None,
                        "generation_time_s": round(gen_time, 2),
                        "tokens_per_sec": round(len(cleaned.split()) * 1.3 / gen_time, 1) if gen_time > 0 else 0,
                    }

                except Exception as e:
                    gen_time = time.time() - gen_start
                    record = {
                        "problem_index": pi,
                        "problem": problem,
                        "category": prompt_obj.get("category", ""),
                        "lens_index": lens_idx,
                        "lens_name": lens["name"],
                        "raw_output": None,
                        "headline": None,
                        "body": None,
                        "error": str(e),
                        "generation_time_s": round(gen_time, 2),
                        "tokens_per_sec": 0,
                    }
                    errors += 1

                out_f.write(json.dumps(record) + "\n")
                out_f.flush()
                completed += 1

                # Progress
                elapsed = time.time() - start_time
                remaining_takes = total_takes - completed
                if completed > len(done_keys):
                    new_completed = completed - len(done_keys)
                    avg_time = elapsed / new_completed
                    eta = timedelta(seconds=int(avg_time * remaining_takes))
                else:
                    eta = "?"

                headline_preview = (record.get("headline") or "ERROR")[:50]
                status = "OK" if record.get("headline") else "ERR"

                print(
                    f"[{completed}/{total_takes}] "
                    f"P{pi} L{lens_idx:2d} {lens['emoji']} {lens['name']:20s} "
                    f"{status} {gen_time:5.1f}s "
                    f"| {headline_preview:50s} "
                    f"| ETA: {eta}"
                )

    # ── Summary ─────────────────────────────────────────────────────────────
    elapsed_total = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"  DONE: {completed} takes in {timedelta(seconds=int(elapsed_total))}")
    print(f"  Errors: {errors}")
    print(f"  Output: {jsonl_path}")
    print(f"{'='*60}\n")

    # Generate HTML report
    print("Generating HTML report...")
    generate_html(jsonl_path, html_path, prompts, lens_indices)
    print(f"Open in browser: {html_path}\n")


if __name__ == "__main__":
    main()
