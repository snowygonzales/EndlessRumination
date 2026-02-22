"""Safety screening — server-side via Claude classification."""

from __future__ import annotations

import anthropic

from app.config import get_settings
from app.models.schemas import CRISIS_RESOURCES

settings = get_settings()

_client: anthropic.AsyncAnthropic | None = None

SAFETY_SYSTEM_PROMPT = (
    "Analyze if this message contains: suicidal ideation, self-harm, "
    "violence toward others, abuse, or content inappropriate for a "
    "psychology wellness app. Respond with SAFE or UNSAFE and a one-word "
    "category if unsafe. Format: SAFE or UNSAFE:<category>"
)


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


async def check_safety(problem: str) -> dict:
    """Run safety classification on user input.

    Returns:
        {"safe": True} or {"safe": False, "category": "...", "resources": [...]}
    """
    client = _get_client()

    message = await client.messages.create(
        model=settings.claude_model,
        max_tokens=50,
        system=SAFETY_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": problem}],
    )

    response_text = message.content[0].text.strip().upper()

    if response_text.startswith("SAFE"):
        return {"safe": True}

    # Parse category from "UNSAFE:category" or just "UNSAFE"
    category = None
    if ":" in response_text:
        category = response_text.split(":", 1)[1].strip().lower()

    return {
        "safe": False,
        "category": category or "flagged",
        "resources": CRISIS_RESOURCES,
    }
