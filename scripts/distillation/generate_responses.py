"""Phase 1.3 — Generate teacher responses from Sonnet for all 20 base lenses.

For each expanded prompt, generate a take from each of the 20 base lenses
using Claude Sonnet as the teacher model. Uses the exact system prompts
from backend/app/lenses/definitions.py.

Usage:
    source backend/.venv/bin/activate
    python scripts/distillation/generate_responses.py

Input:  data/expanded_prompts.jsonl
Output: data/teacher_responses.jsonl

Estimated cost: 800 prompts x 20 lenses = 16,000 API calls ≈ $80-160
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

import anthropic

# Add backend to path so we can import lens definitions directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.lenses.definitions import LENSES, FORMAT_INSTRUCTION

# Load API key from backend .env
_env_path = PROJECT_ROOT / "backend" / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
if not API_KEY:
    print("ERROR: ANTHROPIC_API_KEY not found in environment or backend/.env")
    sys.exit(1)

DATA_DIR = PROJECT_ROOT / "data"
INPUT_PATH = DATA_DIR / "expanded_prompts.jsonl"
OUTPUT_PATH = DATA_DIR / "teacher_responses.jsonl"
PROGRESS_PATH = DATA_DIR / ".generate_responses_progress.json"

# Sonnet model for teacher responses
TEACHER_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 400

# Concurrency: stay within Anthropic rate limits
# Sonnet: 4000 RPM (requests per minute) on paid tier
MAX_CONCURRENT = 20  # conservative
RETRY_MAX = 3
RETRY_DELAY = 5.0


def _parse_take(text: str) -> dict:
    """Parse model response into headline + body (same logic as claude_service.py)."""
    text = text.strip()
    parts = text.split("\n\n", 1)
    if len(parts) == 2:
        return {"headline": parts[0].strip(), "body": parts[1].strip()}
    lines = text.split("\n", 1)
    if len(lines) == 2:
        return {"headline": lines[0].strip(), "body": lines[1].strip()}
    return {"headline": text[:80], "body": text}


async def generate_single_take(
    client: anthropic.AsyncAnthropic,
    problem: str,
    lens: dict,
    semaphore: asyncio.Semaphore,
) -> dict | None:
    """Generate one take for one lens and return the result."""
    async with semaphore:
        for attempt in range(RETRY_MAX):
            try:
                message = await client.messages.create(
                    model=TEACHER_MODEL,
                    max_tokens=MAX_TOKENS,
                    system=lens["system_prompt"],
                    messages=[{"role": "user", "content": problem}],
                )
                text = message.content[0].text
                parsed = _parse_take(text)

                return {
                    "problem": problem,
                    "lens_index": lens["index"],
                    "lens_name": lens["name"],
                    "system_prompt": lens["system_prompt"],
                    "headline": parsed["headline"],
                    "body": parsed["body"],
                    "raw_response": text,
                    "model": TEACHER_MODEL,
                }
            except anthropic.RateLimitError:
                wait = RETRY_DELAY * (2 ** attempt)
                print(f"    Rate limited, waiting {wait:.0f}s...")
                await asyncio.sleep(wait)
            except Exception as e:
                if attempt < RETRY_MAX - 1:
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    print(f"    FAILED lens {lens['index']} after {RETRY_MAX} attempts: {e}")
                    return None
    return None


async def generate_for_prompt(
    client: anthropic.AsyncAnthropic,
    prompt: dict,
    semaphore: asyncio.Semaphore,
) -> list[dict]:
    """Generate takes from all 20 lenses for a single prompt."""
    tasks = [
        generate_single_take(client, prompt["problem"], lens, semaphore)
        for lens in LENSES
    ]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]


def load_progress() -> set[str]:
    """Load set of already-processed problem texts (for resume support)."""
    if PROGRESS_PATH.exists():
        data = json.loads(PROGRESS_PATH.read_text())
        return set(data.get("completed_problems", []))
    return set()


def save_progress(completed: set[str]):
    """Save progress for resume support."""
    PROGRESS_PATH.write_text(json.dumps({
        "completed_problems": list(completed),
        "count": len(completed),
    }))


async def main():
    if not INPUT_PATH.exists():
        print(f"ERROR: {INPUT_PATH} not found. Run expand_seeds.py first.")
        sys.exit(1)

    # Load prompts
    prompts = []
    with open(INPUT_PATH) as f:
        for line in f:
            if line.strip():
                prompts.append(json.loads(line))

    # Load progress (resume support)
    completed = load_progress()
    remaining = [p for p in prompts if p["problem"] not in completed]

    print(f"Loaded {len(prompts)} prompts, {len(completed)} already done, {len(remaining)} remaining")
    print(f"Generating {len(remaining)} x 20 lenses = {len(remaining) * 20} API calls")
    print(f"Estimated cost: ${len(remaining) * 20 * 0.008:.0f}-${len(remaining) * 20 * 0.012:.0f}")
    print(f"Concurrency: {MAX_CONCURRENT} simultaneous requests\n")

    if not remaining:
        print("All prompts already processed! Delete .generate_responses_progress.json to re-run.")
        return

    client = anthropic.AsyncAnthropic(api_key=API_KEY)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    # Open output file in append mode for resume support
    total_generated = 0
    start_time = time.time()

    with open(OUTPUT_PATH, "a") as f:
        for i, prompt in enumerate(remaining):
            results = await generate_for_prompt(client, prompt, semaphore)

            for r in results:
                r["category"] = prompt.get("category", "general")
                r["complexity"] = prompt.get("complexity", 2)
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

            total_generated += len(results)
            completed.add(prompt["problem"])

            # Progress reporting every 10 prompts
            if (i + 1) % 10 == 0 or (i + 1) == len(remaining):
                elapsed = time.time() - start_time
                rate = total_generated / elapsed if elapsed > 0 else 0
                eta = (len(remaining) - i - 1) * 20 / rate if rate > 0 else 0
                print(
                    f"  [{i+1}/{len(remaining)}] "
                    f"{total_generated} takes generated "
                    f"({rate:.1f} takes/s, ETA {eta/60:.0f}m)"
                )
                # Save progress periodically
                save_progress(completed)
                f.flush()

    save_progress(completed)

    print(f"\nDone! {total_generated} teacher responses written to {OUTPUT_PATH}")
    print(f"Total time: {(time.time() - start_time) / 60:.1f} minutes")
    print(f"\nTo clean up progress file: rm {PROGRESS_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
