"""Phase 1.2 — Expand 200 seed prompts to 800-1200 via Opus variations.

For each seed prompt, generates 4-6 variations with different angles,
severity levels, and demographic contexts. Deduplicates near-duplicates.

Usage:
    source backend/.venv/bin/activate
    python scripts/distillation/expand_seeds.py

Input:  data/seed_prompts.jsonl
Output: data/expanded_prompts.jsonl
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import anthropic

# Load API key from backend .env
_env_path = Path(__file__).resolve().parent.parent.parent / "backend" / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
if not API_KEY:
    print("ERROR: ANTHROPIC_API_KEY not found in environment or backend/.env")
    sys.exit(1)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
INPUT_PATH = DATA_DIR / "seed_prompts.jsonl"
OUTPUT_PATH = DATA_DIR / "expanded_prompts.jsonl"

# Concurrency limit to respect API rate limits
# Anthropic output token limit: 8,000 tokens/min on standard tier
# Each expansion request generates ~500-800 output tokens
# 2 concurrent = ~1,000-1,600 tokens/min, well under limit
MAX_CONCURRENT = 2

EXPANSION_PROMPT = """You are generating training data for a mental wellness AI app. Given this original worry prompt, generate 5 VARIATIONS that explore similar themes but from different angles.

Original worry:
\"\"\"{problem}\"\"\"
Category: {category}

Requirements for each variation:
- 20-100 words, realistic inner monologue
- Each variation should be a DISTINCT worry, not a rephrasing of the same one
- Vary: demographic (age, gender, life stage), severity, specificity, tone
- Include specific details (different names, numbers, situations)
- Some should be more articulate, some more raw/messy
- All should feel like real things typed into an app at 2am
- Stay within the same general category but explore different facets

Return ONLY a JSON array of objects with "problem" and "complexity" (1-3):
[
  {{"problem": "...", "complexity": 2}},
  ...
]

Generate exactly 5 variations. Return ONLY valid JSON."""


async def expand_seed(
    client: anthropic.AsyncAnthropic,
    seed: dict,
    semaphore: asyncio.Semaphore,
) -> list[dict]:
    """Generate 5 variations of a single seed prompt."""
    async with semaphore:
        prompt = EXPANSION_PROMPT.format(
            problem=seed["problem"],
            category=seed.get("category", "general"),
        )

        message = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        text = message.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        try:
            variations = json.loads(text)
        except json.JSONDecodeError:
            return []

        for v in variations:
            v["category"] = seed.get("category", "general")
            v["source"] = "expanded"

        return variations


def simple_dedup(prompts: list[dict], threshold: float = 0.85) -> list[dict]:
    """Simple word-overlap deduplication (no heavy deps needed).

    Uses Jaccard similarity on word sets. For production, use sentence
    embeddings, but this is good enough for initial filtering.
    """
    seen = []
    kept = []

    for p in prompts:
        words = set(p["problem"].lower().split())
        is_dup = False
        for seen_words in seen:
            if not words or not seen_words:
                continue
            intersection = len(words & seen_words)
            union = len(words | seen_words)
            if union > 0 and intersection / union > threshold:
                is_dup = True
                break
        if not is_dup:
            seen.append(words)
            kept.append(p)

    return kept


async def main():
    if not INPUT_PATH.exists():
        print(f"ERROR: {INPUT_PATH} not found. Run generate_seeds.py first.")
        sys.exit(1)

    # Load seeds
    seeds = []
    with open(INPUT_PATH) as f:
        for line in f:
            if line.strip():
                seeds.append(json.loads(line))

    print(f"Loaded {len(seeds)} seed prompts")
    print(f"Generating 5 variations each → target ~{len(seeds) * 5} expanded prompts\n")

    client = anthropic.AsyncAnthropic(api_key=API_KEY)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    # Include originals
    all_prompts = []
    for s in seeds:
        all_prompts.append({
            "problem": s["problem"],
            "category": s.get("category", "general"),
            "complexity": s.get("complexity", 2),
            "source": "seed",
        })

    # Expand in parallel (with concurrency limit)
    tasks = [expand_seed(client, seed, semaphore) for seed in seeds]

    completed = 0
    for coro in asyncio.as_completed(tasks):
        try:
            variations = await coro
            all_prompts.extend(variations)
            completed += 1
            if completed % 20 == 0:
                print(f"  Expanded {completed}/{len(seeds)} seeds ({len(all_prompts)} total prompts)")
        except Exception as e:
            completed += 1
            print(f"  WARNING: Expansion failed: {e}")

    print(f"\nTotal before dedup: {len(all_prompts)}")

    # Deduplicate
    deduped = simple_dedup(all_prompts)
    print(f"Total after dedup:  {len(deduped)}")

    # Write output
    with open(OUTPUT_PATH, "w") as f:
        for p in deduped:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    print(f"\nDone! {len(deduped)} prompts written to {OUTPUT_PATH}")

    # Summary
    by_category = {}
    for p in deduped:
        cat = p.get("category", "unknown")
        by_category[cat] = by_category.get(cat, 0) + 1
    print("\nBreakdown by category:")
    for cat, count in sorted(by_category.items()):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
