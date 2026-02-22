"""Claude API integration — single take + batch streaming."""

from __future__ import annotations

import asyncio
import json
from typing import AsyncGenerator

import anthropic

from app.config import get_settings
from app.lenses.definitions import get_lens

settings = get_settings()

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


def _parse_take(text: str) -> dict:
    """Parse Claude's response into headline + body.

    Expected format:
        Punchy headline here

        Body text spanning 3-5 sentences.
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


async def generate_take(problem: str, lens_index: int) -> dict:
    """Generate a single take (non-streaming) and return parsed result."""
    client = _get_client()
    lens = get_lens(lens_index)

    message = await client.messages.create(
        model=settings.claude_model,
        max_tokens=settings.claude_max_tokens,
        system=lens["system_prompt"],
        messages=[{"role": "user", "content": problem}],
    )

    text = message.content[0].text
    parsed = _parse_take(text)
    return {"lens_index": lens_index, **parsed}


async def generate_take_streaming(
    problem: str, lens_index: int
) -> AsyncGenerator[str, None]:
    """Generate a single take with streaming, yielding SSE events."""
    client = _get_client()
    lens = get_lens(lens_index)

    collected = ""
    async with client.messages.stream(
        model=settings.claude_model,
        max_tokens=settings.claude_max_tokens,
        system=lens["system_prompt"],
        messages=[{"role": "user", "content": problem}],
    ) as stream:
        async for text in stream.text_stream:
            collected += text

    parsed = _parse_take(collected)
    result = {"lens_index": lens_index, **parsed}
    yield f"data: {json.dumps(result)}\n\n"


async def _generate_single(problem: str, lens_index: int) -> dict:
    """Internal: generate one take, return parsed dict."""
    return await generate_take(problem, lens_index)


async def generate_batch_streaming(
    problem: str, lens_indices: list[int]
) -> AsyncGenerator[str, None]:
    """Fire parallel Claude calls in batches. Yield SSE events as they complete."""
    batch_size = settings.parallel_batch_size

    for i in range(0, len(lens_indices), batch_size):
        batch = lens_indices[i : i + batch_size]
        tasks = [_generate_single(problem, idx) for idx in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                # Skip failed takes, log in production
                continue
            yield f"data: {json.dumps(result)}\n\n"

    yield "data: [DONE]\n\n"
