"""Post formatting — assembles takes into platform-ready posts with character limits."""
from __future__ import annotations

from social.generate import Take

# Character limits per platform
X_CHAR_LIMIT = 280
BLUESKY_CHAR_LIMIT = 300

# Fixed elements
HASHTAG = "#EndlessRumination"


def _char_count(text: str) -> int:
    """Count characters. URLs on X are always counted as 23 chars (t.co wrapping)."""
    return len(text)


def _truncate_at_sentence(text: str, max_chars: int) -> str:
    """Truncate text at the nearest sentence boundary within max_chars.

    Falls back to word boundary if no sentence break fits.
    """
    if len(text) <= max_chars:
        return text

    # Try sentence boundaries (. ! ?)
    truncated = text[:max_chars]
    for sep in [". ", "! ", "? "]:
        last = truncated.rfind(sep)
        if last > 0:
            return truncated[: last + 1].rstrip()

    # Fall back to word boundary
    last_space = truncated.rfind(" ")
    if last_space > 0:
        return truncated[:last_space].rstrip() + "..."

    return truncated[:max_chars - 3] + "..."


def format_single_post(
    take: Take,
    app_link: str = "",
    platform: str = "x",
) -> str:
    """Format a take as a single social media post.

    Structure:
        {emoji} {lens_name}:
        "{headline}"

        {body}

        #EndlessRumination
        {link}
    """
    limit = X_CHAR_LIMIT if platform == "x" else BLUESKY_CHAR_LIMIT

    # Build fixed parts
    header = f"{take.lens_emoji} {take.lens_name}:"
    quoted_headline = f"\"{take.headline}\""

    # Calculate space for body
    # Structure: header\nheadline\n\nbody\n\nhashtag[\nlink]
    fixed_parts = [header, quoted_headline, "", HASHTAG]
    if app_link:
        fixed_parts.append(app_link)

    fixed_text = "\n".join(fixed_parts)
    # +1 for the \n before body, +1 for \n after body
    fixed_len = len(fixed_text) + 2  # two newlines around body slot

    available = limit - fixed_len
    if available < 20:
        # Not enough room for body — just do header + headline + hashtag
        parts = [header, quoted_headline, "", HASHTAG]
        if app_link:
            parts.append(app_link)
        return "\n".join(parts)

    body = _truncate_at_sentence(take.body, available)

    parts = [header, quoted_headline, "", body, "", HASHTAG]
    if app_link:
        parts.append(app_link)

    return "\n".join(parts)


def format_thread_opener(
    problem: str,
    lens_names: list[str],
    platform: str = "x",
) -> str:
    """Format the first post of a thread — the problem statement.

    Structure:
        What if {N} different personas reacted to:

        "{problem_truncated}"

        Here's what {names} had to say...
    """
    limit = X_CHAR_LIMIT if platform == "x" else BLUESKY_CHAR_LIMIT

    count = len(lens_names)
    names_str = ", ".join(lens_names[:-1]) + f" & {lens_names[-1]}" if count > 1 else lens_names[0]

    intro = f"What if {count} different personas reacted to:"
    outro = f"Here's what {names_str} had to say \U0001f9f5\U0001f447\n\n#EndlessRumination"

    # Calculate space for problem
    fixed_len = len(intro) + 4 + len(outro) + 4  # newlines + quotes
    available = limit - fixed_len

    truncated_problem = _truncate_at_sentence(problem, available)

    return f"{intro}\n\n\"{truncated_problem}\"\n\n{outro}"


def format_thread_reply(
    take: Take,
    index: int,
    total: int,
    platform: str = "x",
) -> str:
    """Format a reply in a thread.

    Structure:
        {emoji} {lens_name} ({index}/{total}):
        {headline}

        {body}
    """
    limit = X_CHAR_LIMIT if platform == "x" else BLUESKY_CHAR_LIMIT

    header = f"{take.lens_emoji} {take.lens_name} ({index}/{total}):"
    headline = take.headline

    # Calculate space for body
    fixed_len = len(header) + 1 + len(headline) + 2  # newlines
    available = limit - fixed_len

    if available < 20:
        return f"{header}\n{headline}"

    body = _truncate_at_sentence(take.body, available)
    return f"{header}\n{headline}\n\n{body}"


def format_announcement(
    version: str,
    notes: str,
    app_link: str = "",
    platform: str = "x",
) -> str:
    """Format a version announcement post.

    Structure:
        Endless Rumination v{version} is here!

        What's new:
        {notes}

        Describe a problem. Doom-scroll through AI wisdom.

        #EndlessRumination
        {link}
    """
    limit = X_CHAR_LIMIT if platform == "x" else BLUESKY_CHAR_LIMIT

    header = f"\U0001f680 Endless Rumination v{version} is here!"
    tagline = "Describe a problem. Doom-scroll through AI wisdom."

    footer_parts = [HASHTAG]
    if app_link:
        footer_parts.append(app_link)
    footer = "\n".join(footer_parts)

    # Calculate space for notes
    fixed_len = len(header) + len(tagline) + len(footer) + 12  # newlines + "What's new:\n"
    available = limit - fixed_len

    truncated_notes = _truncate_at_sentence(notes, available)

    return f"{header}\n\n\u2728 What's new:\n{truncated_notes}\n\n{tagline}\n\n{footer}"
