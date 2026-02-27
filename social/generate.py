"""Take generation via Claude API — reuses lens definitions from the backend."""
from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import anthropic

from social.config import SocialConfig

# ---------------------------------------------------------------------------
# Import lens definitions from the backend without importing backend services
# ---------------------------------------------------------------------------
_BACKEND_DIR = str(Path(__file__).resolve().parent.parent / "backend")
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from app.lenses.definitions import FORMAT_INSTRUCTION, LENSES  # noqa: E402
from app.lenses.voice_packs import VOICE_PACKS  # noqa: E402

# ---------------------------------------------------------------------------
# Social-optimized format instruction (shorter output for character limits)
# ---------------------------------------------------------------------------
SOCIAL_FORMAT_INSTRUCTION = """
RESPOND IN EXACTLY THIS FORMAT:
First line: A punchy headline under 10 words. No quotes around it.
Then one blank line.
Then 1-2 sentences of sharp perspective on their specific problem. Keep the body under 180 characters.
Nothing else. No markdown. No asterisks. No labels like "Headline:" or "Body:".
""".strip()


@dataclass
class Take:
    """A generated take — headline + body from a specific lens."""

    lens_index: int
    lens_name: str
    lens_emoji: str
    headline: str
    body: str


def get_all_lenses() -> list[dict]:
    """Return flat list of all 40 lenses (20 base + 20 voice pack voices)."""
    all_lenses: list[dict] = list(LENSES)
    for pack in VOICE_PACKS:
        all_lenses.extend(pack["voices"])
    return all_lenses


def get_lens(index: int) -> dict:
    """Get a lens by index (0-39)."""
    all_lenses = get_all_lenses()
    for lens in all_lenses:
        if lens["index"] == index:
            return lens
    raise ValueError(f"No lens with index {index}")


def pick_random_lens(exclude_indices: Optional[list[int]] = None) -> dict:
    """Pick a random lens, optionally excluding certain indices."""
    all_lenses = get_all_lenses()
    if exclude_indices:
        all_lenses = [l for l in all_lenses if l["index"] not in exclude_indices]
    return random.choice(all_lenses)


def pick_random_lenses(count: int = 3, exclude_indices: Optional[list[int]] = None) -> list[dict]:
    """Pick N unique random lenses."""
    all_lenses = get_all_lenses()
    if exclude_indices:
        all_lenses = [l for l in all_lenses if l["index"] not in exclude_indices]
    return random.sample(all_lenses, min(count, len(all_lenses)))


def _parse_take(text: str) -> dict:
    """Parse Claude's response into headline + body.

    Expected format:
        Punchy headline here

        Body text in 1-2 sentences.
    """
    text = text.strip()
    parts = text.split("\n\n", 1)
    if len(parts) == 2:
        return {"headline": parts[0].strip(), "body": parts[1].strip()}
    # Fallback: first line is headline, rest is body
    lines = text.split("\n", 1)
    if len(lines) == 2:
        return {"headline": lines[0].strip(), "body": lines[1].strip()}
    return {"headline": text[:80], "body": text}


def _make_social_prompt(lens: dict) -> str:
    """Build a social-media-optimized system prompt from a lens.

    Replaces the standard FORMAT_INSTRUCTION with a shorter one that produces
    output suitable for social media character limits.
    """
    original = lens["system_prompt"]
    # Replace the format instruction with our social variant
    if FORMAT_INSTRUCTION in original:
        return original.replace(FORMAT_INSTRUCTION, SOCIAL_FORMAT_INSTRUCTION)
    # Fallback: append social format instruction
    return f"{original}\n\n{SOCIAL_FORMAT_INSTRUCTION}"


def generate_take(problem: str, lens: dict, config: SocialConfig) -> Take:
    """Generate a single take via Claude API (synchronous).

    Args:
        problem: The everyday problem to react to.
        lens: Lens definition dict (from LENSES or VOICE_PACKS).
        config: Social bot configuration.

    Returns:
        A Take dataclass with headline, body, and lens metadata.
    """
    client = anthropic.Anthropic(api_key=config.anthropic_api_key)

    message = client.messages.create(
        model=config.claude_model,
        max_tokens=config.claude_max_tokens,
        system=_make_social_prompt(lens),
        messages=[{"role": "user", "content": problem}],
    )

    text = message.content[0].text
    parsed = _parse_take(text)

    return Take(
        lens_index=lens["index"],
        lens_name=lens["name"],
        lens_emoji=lens.get("emoji", ""),
        headline=parsed["headline"],
        body=parsed["body"],
    )


def generate_takes(
    problem: str, lenses: list[dict], config: SocialConfig
) -> list[Take]:
    """Generate takes from multiple lenses (sequential, synchronous)."""
    takes: list[Take] = []
    for lens in lenses:
        take = generate_take(problem, lens, config)
        takes.append(take)
    return takes
