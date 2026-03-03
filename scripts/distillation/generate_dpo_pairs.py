"""Phase 1.5 — Generate DPO preference pairs for alignment training.

For a subset of prompts, generates intentionally "bad" responses alongside
the good ones from Phase 1.3/1.4. These teach the model what NOT to do:
  - Generic responses that ignore the specific problem
  - Wrong-persona responses (therapist talking like comedian)
  - Format violations (markdown, labels, wrong length)
  - Surface-level takes that don't engage deeply

Usage:
    source backend/.venv/bin/activate
    python scripts/distillation/generate_dpo_pairs.py

Input:  data/filtered_responses.jsonl
Output: data/dpo_pairs.jsonl
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import sys
import time
from pathlib import Path

import anthropic

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.lenses.definitions import LENSES

# Load API key
_env_path = PROJECT_ROOT / "backend" / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
if not API_KEY:
    print("ERROR: ANTHROPIC_API_KEY not found")
    sys.exit(1)

DATA_DIR = PROJECT_ROOT / "data"
INPUT_PATH = DATA_DIR / "filtered_responses.jsonl"
OUTPUT_PATH = DATA_DIR / "dpo_pairs.jsonl"

TEACHER_MODEL = "claude-sonnet-4-20250514"
MAX_CONCURRENT = 10
TARGET_PAIRS = 2000  # DPO pairs to generate

# Bad response generation strategies
BAD_STRATEGIES = [
    {
        "name": "generic",
        "instruction": (
            "Generate a GENERIC motivational response that could apply to ANY problem. "
            "Do NOT reference any specific details from the user's worry. Use vague platitudes "
            "like 'everything happens for a reason' and 'this too shall pass'. "
            "Keep the same persona voice but make it completely non-specific."
        ),
    },
    {
        "name": "wrong_persona",
        "instruction": (
            "Generate a response but use the WRONG persona voice. If the persona is a comedian, "
            "respond like a dry academic. If it's a therapist, respond like a drill sergeant. "
            "If it's a philosopher, respond like a five-year-old. The content should be vaguely "
            "relevant but the voice should be completely wrong for this persona."
        ),
    },
    {
        "name": "format_violation",
        "instruction": (
            "Generate a response that VIOLATES the expected format. Use markdown headers, "
            "bullet points, bold text with **asterisks**, and labels like 'Headline:' and 'Body:'. "
            "Make the headline too long (20+ words). Add a disclaimer at the end about seeking "
            "professional help. The content can be okay but the format must be wrong."
        ),
    },
    {
        "name": "shallow",
        "instruction": (
            "Generate a response that is SURFACE-LEVEL. Acknowledge the problem in one sentence, "
            "then immediately jump to generic advice. Don't sit with the emotion, don't reframe, "
            "don't apply the persona's unique worldview. Just give obvious advice that anyone "
            "would give. Make it feel like a fortune cookie, not a fresh perspective."
        ),
    },
]


async def generate_bad_response(
    client: anthropic.AsyncAnthropic,
    problem: str,
    lens: dict,
    strategy: dict,
    semaphore: asyncio.Semaphore,
) -> str | None:
    """Generate an intentionally bad response for DPO."""
    async with semaphore:
        system_prompt = (
            f"You are generating a deliberately MEDIOCRE response for training data. "
            f"The persona is: {lens['name']}.\n\n"
            f"Strategy: {strategy['instruction']}\n\n"
            f"RESPOND IN THIS FORMAT:\n"
            f"First line: A headline.\n"
            f"Then one blank line.\n"
            f"Then a few sentences.\n"
            f"Nothing else."
        )

        for attempt in range(3):
            try:
                message = await client.messages.create(
                    model=TEACHER_MODEL,
                    max_tokens=400,
                    system=system_prompt,
                    messages=[{"role": "user", "content": problem}],
                )
                return message.content[0].text.strip()
            except anthropic.RateLimitError:
                await asyncio.sleep(5 * (2 ** attempt))
            except Exception:
                if attempt == 2:
                    return None
                await asyncio.sleep(2)
    return None


async def main():
    if not INPUT_PATH.exists():
        print(f"ERROR: {INPUT_PATH} not found. Run filter_quality.py first.")
        sys.exit(1)

    # Load filtered responses (these are the "chosen" / good responses)
    responses = []
    with open(INPUT_PATH) as f:
        for line in f:
            if line.strip():
                responses.append(json.loads(line))

    print(f"Loaded {len(responses)} filtered responses")

    # Sample responses for DPO (pick diverse subset)
    # Group by problem to avoid over-representing any single problem
    by_problem: dict[str, list[dict]] = {}
    for r in responses:
        by_problem.setdefault(r["problem"], []).append(r)

    # Select up to TARGET_PAIRS responses, sampling across problems
    selected = []
    problems = list(by_problem.keys())
    random.shuffle(problems)

    for problem in problems:
        if len(selected) >= TARGET_PAIRS:
            break
        group = by_problem[problem]
        # Take up to 5 responses per problem (different lenses)
        sample = random.sample(group, min(5, len(group)))
        selected.extend(sample)

    selected = selected[:TARGET_PAIRS]
    print(f"Selected {len(selected)} responses for DPO pair generation")
    print(f"Using {len(BAD_STRATEGIES)} bad-response strategies\n")

    client = anthropic.AsyncAnthropic(api_key=API_KEY)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    # Generate bad responses for each selected good response
    pairs = []
    start_time = time.time()

    for i, good_response in enumerate(selected):
        # Pick a random bad strategy
        strategy = random.choice(BAD_STRATEGIES)

        # Find the matching lens
        lens_index = good_response["lens_index"]
        lens = LENSES[lens_index] if lens_index < 20 else {"name": good_response["lens_name"]}

        bad_text = await generate_bad_response(
            client,
            good_response["problem"],
            lens,
            strategy,
            semaphore,
        )

        if bad_text:
            pair = {
                "problem": good_response["problem"],
                "lens_index": lens_index,
                "lens_name": good_response["lens_name"],
                "system_prompt": good_response["system_prompt"],
                "chosen": f"{good_response['headline']}\n\n{good_response['body']}",
                "rejected": bad_text,
                "reject_strategy": strategy["name"],
            }
            pairs.append(pair)

        if (i + 1) % 50 == 0 or (i + 1) == len(selected):
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            print(f"  [{i+1}/{len(selected)}] {len(pairs)} pairs generated ({rate:.1f}/s)")

    # Write output
    with open(OUTPUT_PATH, "w") as f:
        for pair in pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    print(f"\nDone! {len(pairs)} DPO pairs written to {OUTPUT_PATH}")
    print(f"Time: {(time.time() - start_time) / 60:.1f} minutes")

    # Strategy distribution
    strat_counts: dict[str, int] = {}
    for p in pairs:
        s = p["reject_strategy"]
        strat_counts[s] = strat_counts.get(s, 0) + 1
    print("\nRejection strategy distribution:")
    for s, c in sorted(strat_counts.items()):
        print(f"  {s}: {c}")


if __name__ == "__main__":
    asyncio.run(main())
