"""Shared cost tracker across distillation pipeline steps 1.3–1.5.

All three scripts (generate_responses, filter_quality, generate_dpo_pairs)
share a single $100 USD budget. Each script reads the cumulative spend on
startup and writes back its own spend on completion (or early stop).

Tracker file: data/.pipeline_cost_tracker.json
"""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TRACKER_PATH = PROJECT_ROOT / "data" / ".pipeline_cost_tracker.json"

# Shared cap across steps 1.3 + 1.4 + 1.5
PIPELINE_COST_CAP_USD = 100.0

# Per-call cost estimates
# Sonnet: ~500 input tokens ($0.0015) + ~300 output tokens ($0.0045) = ~$0.006
# Haiku:  ~500 input tokens ($0.00005) + ~200 output tokens ($0.0005) = ~$0.00055
COST_SONNET_CALL = 0.006
COST_HAIKU_CALL = 0.00055

# Per-step budget reservations (must sum to PIPELINE_COST_CAP_USD)
# 1.3 generate_responses: Sonnet, ~833 prompts × 20 lenses — heaviest step
# 1.4 filter_quality:     Haiku, ~16K responses — cheap
# 1.5 generate_dpo_pairs: Sonnet, ~2000 pairs — moderate
STEP_BUDGETS = {
    "generate_responses": 78.0,   # ~13,000 Sonnet calls → ~650 prompts × 20 lenses
    "filter_quality": 10.0,       # ~18,000 Haiku calls — plenty of headroom
    "generate_dpo_pairs": 12.0,   # ~2,000 Sonnet calls
}


def load_tracker() -> dict:
    """Load the pipeline cost tracker. Returns dict with total_spent and per-step breakdown."""
    if TRACKER_PATH.exists():
        return json.loads(TRACKER_PATH.read_text())
    return {
        "cap_usd": PIPELINE_COST_CAP_USD,
        "total_spent": 0.0,
        "steps": {},
    }


def save_tracker(tracker: dict):
    """Persist the cost tracker to disk."""
    TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)
    TRACKER_PATH.write_text(json.dumps(tracker, indent=2))


def remaining_budget(tracker: dict | None = None) -> float:
    """Return how much of the overall pipeline budget remains."""
    if tracker is None:
        tracker = load_tracker()
    return max(0.0, PIPELINE_COST_CAP_USD - tracker["total_spent"])


def step_budget(step_name: str, tracker: dict | None = None) -> float:
    """Return how much budget a specific step can still spend.

    This is the MINIMUM of:
      - The step's reserved allocation minus what it already spent
      - The overall remaining pipeline budget
    This ensures no single step starves the others.
    """
    if tracker is None:
        tracker = load_tracker()
    allocation = STEP_BUDGETS.get(step_name, 0.0)
    already_spent = tracker["steps"].get(step_name, 0.0)
    step_remaining = max(0.0, allocation - already_spent)
    pipeline_remaining = remaining_budget(tracker)
    return min(step_remaining, pipeline_remaining)


def record_spend(step_name: str, amount: float):
    """Add spend for a step and save."""
    tracker = load_tracker()
    prev = tracker["steps"].get(step_name, 0.0)
    tracker["steps"][step_name] = prev + amount
    tracker["total_spent"] = sum(tracker["steps"].values())
    save_tracker(tracker)
    return tracker


def print_budget_status(tracker: dict | None = None):
    """Print current budget usage."""
    if tracker is None:
        tracker = load_tracker()
    spent = tracker["total_spent"]
    cap = PIPELINE_COST_CAP_USD
    left = remaining_budget(tracker)
    print(f"Pipeline budget: ${spent:.2f} / ${cap:.0f} spent (${left:.2f} remaining)")
    if tracker.get("steps"):
        for step, amt in tracker["steps"].items():
            print(f"  {step}: ${amt:.2f}")
    print()
