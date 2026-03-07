"""Phase 1.1 — Generate 200 seed worry prompts across 10 categories.

Uses Claude Opus to generate realistic, specific worry prompts that feel
like things real people actually think at 2am.

Usage:
    source backend/.venv/bin/activate
    python scripts/distillation/generate_seeds.py

Output: data/seed_prompts.jsonl
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

OUTPUT_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "seed_prompts.jsonl"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

CATEGORIES = [
    ("career", "Career and work anxiety — layoffs, imposter syndrome, bad bosses, job interviews, promotions, burnout, career changes, toxic coworkers, performance reviews"),
    ("relationships", "Relationship worries — romantic conflict, breakups, loneliness, rejection, trust issues, communication failures, dating anxiety, long-distance, infidelity fears"),
    ("health", "Health and body anxiety — mortality, aging, illness, medical tests, chronic conditions, body image, fitness, sleep problems, mysterious symptoms"),
    ("financial", "Financial stress — debt, rent, unexpected expenses, retirement fears, lifestyle comparison, investment losses, job insecurity, supporting family"),
    ("family", "Family and parenting concerns — aging parents, sibling conflict, parenting guilt, family expectations, estrangement, in-laws, generational trauma, custody"),
    ("social", "Social anxiety — judgment, comparison, embarrassment, public speaking, fitting in, social media pressure, awkward interactions, reputation"),
    ("academic", "Academic and learning stress — exams, deadlines, thesis pressure, dropping out, competition, feeling stupid, choosing wrong major, student debt"),
    ("existential", "Existential dread — purpose, meaning, legacy, death anxiety, midlife crisis, feeling stuck, questioning life choices, cosmic insignificance"),
    ("decisions", "Decision paralysis — big life choices, FOMO, moving cities, changing careers, ending relationships, having kids, saying yes vs no"),
    ("self_worth", "Self-worth and identity — not being good enough, comparing to others, perfectionism, past mistakes, regret, shame, feeling like a fraud"),
]

SEED_GENERATION_PROMPT = """Generate exactly 20 unique worry prompts for the category: {category_name}.

Context: {category_description}

Each prompt should be a realistic inner monologue — the kind of thing someone would type into a mental wellness app at 2am. They should feel raw, specific, and real.

Requirements:
- Each prompt is 20-100 words
- Vary the tone: some desperate, some casual, some articulate, some messy
- Include specific details (names, numbers, situations) — not generic
- Mix severity: some minor daily anxieties, some deep existential ones
- Mix demographics: different ages, life stages, backgrounds
- NO generic prompts like "I'm worried about my future" — always specific
- Each prompt should be a self-contained worry that a person would type

Return ONLY a JSON array of objects, each with "problem" and "complexity" (1-3, where 1=daily micro-anxiety, 2=moderate ongoing worry, 3=deep existential concern):

[
  {{"problem": "I've been at my job for 3 years and just found out the new hire makes $20k more than me. I've been too scared to ask for a raise because my manager is passive-aggressive and I'm worried she'll find a reason to let me go if I push back.", "complexity": 2}},
  ...
]

Generate exactly 20 prompts. Return ONLY valid JSON, no other text."""


async def generate_seeds_for_category(
    client: anthropic.AsyncAnthropic,
    category_name: str,
    category_description: str,
) -> list[dict]:
    """Generate 20 seed prompts for one category."""
    prompt = SEED_GENERATION_PROMPT.format(
        category_name=category_name,
        category_description=category_description,
    )

    message = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text.strip()
    # Handle potential markdown code blocks
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        prompts = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  WARNING: Failed to parse JSON for {category_name}: {e}")
        print(f"  Raw text (first 200 chars): {text[:200]}")
        return []

    # Add category metadata
    for p in prompts:
        p["category"] = category_name

    return prompts


async def main():
    client = anthropic.AsyncAnthropic(api_key=API_KEY)
    all_seeds = []

    print(f"Generating seed prompts across {len(CATEGORIES)} categories...")
    print(f"Target: 200 prompts (20 per category)\n")

    for category_name, category_desc in CATEGORIES:
        print(f"  [{category_name}] Generating 20 seeds...", end=" ", flush=True)
        try:
            seeds = await generate_seeds_for_category(client, category_name, category_desc)
            all_seeds.extend(seeds)
            print(f"OK ({len(seeds)} prompts)")
        except Exception as e:
            print(f"FAILED: {e}")

    # Write output
    with open(OUTPUT_PATH, "w") as f:
        for seed in all_seeds:
            f.write(json.dumps(seed, ensure_ascii=False) + "\n")

    print(f"\nDone! {len(all_seeds)} seed prompts written to {OUTPUT_PATH}")

    # Summary
    by_category = {}
    for s in all_seeds:
        cat = s.get("category", "unknown")
        by_category[cat] = by_category.get(cat, 0) + 1
    print("\nBreakdown by category:")
    for cat, count in sorted(by_category.items()):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
