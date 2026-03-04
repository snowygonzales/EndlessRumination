"""Phase 1.4 — Quality filter teacher responses via Haiku scoring.

Scores each response on 4 dimensions (1-5) using Claude Haiku:
  - Persona authenticity: Does it sound like the persona?
  - Problem specificity: Does it engage with THIS specific problem?
  - Emotional impact: Would this shift someone's perspective?
  - Safety: No harmful advice (pass/fail)

Keeps only responses scoring 4+ on all dimensions.
Shares a $100 pipeline budget with steps 1.3 and 1.5 via cost_tracker.

Usage:
    source backend/.venv/bin/activate
    python scripts/distillation/filter_quality.py

Input:  data/teacher_responses.jsonl
Output: data/filtered_responses.jsonl
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

import anthropic

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.distillation.cost_tracker import (
    COST_HAIKU_CALL,
    load_tracker,
    print_budget_status,
    record_spend,
    step_budget,
)

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
INPUT_PATH = DATA_DIR / "teacher_responses.jsonl"
OUTPUT_PATH = DATA_DIR / "filtered_responses.jsonl"
REJECTED_PATH = DATA_DIR / "rejected_responses.jsonl"

SCORER_MODEL = "claude-haiku-4-5-20251001"
MAX_CONCURRENT = 30  # Haiku has higher rate limits
RETRY_MAX = 3

STEP_NAME = "filter_quality"

SCORING_PROMPT = """Score this AI-generated response on 4 dimensions. The response is from a persona-based wellness app that gives users fresh perspectives on their worries.

PERSONA: {lens_name}
USER'S WORRY: {problem}

RESPONSE:
{headline}

{body}

Score each dimension 1-5:

1. PERSONA AUTHENTICITY — Does this genuinely sound like {lens_name}? Does it use vocabulary, rhetorical devices, and reasoning patterns consistent with this persona? (1=generic, 5=unmistakably this persona)

2. PROBLEM SPECIFICITY — Does the response engage with THIS specific worry, referencing details from the user's text? Or could it apply to any problem? (1=completely generic, 5=deeply tailored)

3. EMOTIONAL IMPACT — Would reading this actually shift someone's perspective or make them feel something? Is the headline punchy? (1=forgettable, 5=powerful reframe)

4. SAFETY — Is the response safe for a wellness app? No harmful advice, no dismissing real distress, no encouraging dangerous behavior. (1=unsafe, 5=safe)

Also check FORMAT:
- Headline under 12 words? (yes/no)
- Body is 3-5 sentences? (yes/no)
- No markdown, asterisks, or labels? (yes/no)

Return ONLY valid JSON:
{{"persona": <1-5>, "specificity": <1-5>, "impact": <1-5>, "safety": <1-5>, "format_ok": <true/false>}}"""


async def score_response(
    client: anthropic.AsyncAnthropic,
    response: dict,
    semaphore: asyncio.Semaphore,
) -> dict | None:
    """Score a single response using Haiku."""
    async with semaphore:
        prompt = SCORING_PROMPT.format(
            lens_name=response["lens_name"],
            problem=response["problem"],
            headline=response["headline"],
            body=response["body"],
        )

        for attempt in range(RETRY_MAX):
            try:
                message = await client.messages.create(
                    model=SCORER_MODEL,
                    max_tokens=200,
                    messages=[{"role": "user", "content": prompt}],
                )
                text = message.content[0].text.strip()

                # Extract JSON from response
                if text.startswith("```"):
                    text = text.split("\n", 1)[1]
                    if text.endswith("```"):
                        text = text[:-3]
                    text = text.strip()

                scores = json.loads(text)
                return scores

            except (json.JSONDecodeError, anthropic.RateLimitError) as e:
                if isinstance(e, anthropic.RateLimitError):
                    await asyncio.sleep(5 * (2 ** attempt))
                elif attempt < RETRY_MAX - 1:
                    await asyncio.sleep(2)
                else:
                    return None
            except Exception:
                if attempt < RETRY_MAX - 1:
                    await asyncio.sleep(2)
                else:
                    return None
    return None


def passes_filter(scores: dict, min_score: int = 4) -> bool:
    """Check if a response passes the quality filter."""
    if not scores:
        return False
    if not scores.get("format_ok", False):
        return False
    for dim in ["persona", "specificity", "impact", "safety"]:
        if scores.get(dim, 0) < min_score:
            return False
    return True


async def main():
    if not INPUT_PATH.exists():
        print(f"ERROR: {INPUT_PATH} not found. Run generate_responses.py first.")
        sys.exit(1)

    # Load responses
    responses = []
    with open(INPUT_PATH) as f:
        for line in f:
            if line.strip():
                responses.append(json.loads(line))

    print(f"Loaded {len(responses)} teacher responses")

    # Shared pipeline budget — this step's allocation
    tracker = load_tracker()
    print_budget_status(tracker)
    budget_left = step_budget(STEP_NAME, tracker)
    if budget_left <= 0:
        print(f"Budget for {STEP_NAME} exhausted. No calls will be made.")
        return

    estimated_cost = len(responses) * COST_HAIKU_CALL
    max_responses = int(budget_left / COST_HAIKU_CALL)
    if len(responses) > max_responses:
        print(f"Budget left: ${budget_left:.2f} → can score {max_responses} of {len(responses)} responses")
        print(f"Trimming to {max_responses} responses to stay under budget")
        responses = responses[:max_responses]
        estimated_cost = max_responses * COST_HAIKU_CALL

    print(f"Scoring with {SCORER_MODEL} (max concurrent: {MAX_CONCURRENT})")
    print(f"Estimated step cost: ~${estimated_cost:.2f}\n")

    client = anthropic.AsyncAnthropic(api_key=API_KEY)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    # Score all responses
    kept = []
    rejected = []
    estimated_spend = 0.0
    score_distribution = {"persona": [], "specificity": [], "impact": [], "safety": []}
    start_time = time.time()

    # Process in batches for progress reporting
    batch_size = 100
    for batch_start in range(0, len(responses), batch_size):
        batch = responses[batch_start:batch_start + batch_size]
        tasks = [score_response(client, r, semaphore) for r in batch]
        scores_list = await asyncio.gather(*tasks)

        for response, scores in zip(batch, scores_list):
            if scores is None:
                rejected.append({**response, "scores": None, "reject_reason": "scoring_failed"})
                continue

            response["scores"] = scores

            for dim in score_distribution:
                if dim in scores:
                    score_distribution[dim].append(scores[dim])

            if passes_filter(scores):
                kept.append(response)
            else:
                reasons = []
                if not scores.get("format_ok", False):
                    reasons.append("format")
                for dim in ["persona", "specificity", "impact", "safety"]:
                    if scores.get(dim, 0) < 4:
                        reasons.append(f"{dim}={scores.get(dim, '?')}")
                response["reject_reason"] = ", ".join(reasons)
                rejected.append(response)

        estimated_spend += len(batch) * COST_HAIKU_CALL
        elapsed = time.time() - start_time
        processed = batch_start + len(batch)
        rate = processed / elapsed if elapsed > 0 else 0
        print(
            f"  [{processed}/{len(responses)}] "
            f"kept={len(kept)} rejected={len(rejected)} "
            f"(~${estimated_spend:.2f} spent, {rate:.1f} responses/s)"
        )

        # Hard stop if approaching pipeline budget
        if estimated_spend >= budget_left * 0.95:
            print(f"\n  BUDGET LIMIT REACHED (~${estimated_spend:.2f} of ${budget_left:.2f} remaining). Stopping.")
            break

    # Write kept
    with open(OUTPUT_PATH, "w") as f:
        for r in kept:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Write rejected (for analysis)
    with open(REJECTED_PATH, "w") as f:
        for r in rejected:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    record_spend(STEP_NAME, estimated_spend)

    # Summary
    survival_rate = len(kept) / len(responses) * 100 if responses else 0
    print(f"\nDone! Survival rate: {survival_rate:.0f}%")
    print(f"  Kept:     {len(kept)} → {OUTPUT_PATH}")
    print(f"  Rejected: {len(rejected)} → {REJECTED_PATH}")
    print(f"  Step spend: ~${estimated_spend:.2f}")
    print(f"  Time: {(time.time() - start_time) / 60:.1f} minutes")
    print_budget_status()

    # Score distribution
    print("\nScore distribution (avg):")
    for dim, vals in score_distribution.items():
        if vals:
            avg = sum(vals) / len(vals)
            print(f"  {dim}: {avg:.2f} (min={min(vals)}, max={max(vals)})")

    # Rejection reasons
    reason_counts: dict[str, int] = {}
    for r in rejected:
        reason = r.get("reject_reason", "unknown")
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    if reason_counts:
        print("\nTop rejection reasons:")
        for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1])[:10]:
            print(f"  {reason}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
