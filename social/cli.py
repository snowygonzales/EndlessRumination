"""Click CLI for the Endless Rumination social media bot."""
from __future__ import annotations

import sys
from typing import Optional

import click

from social.config import SocialConfig, load_config
from social.format import (
    format_announcement,
    format_single_post,
    format_thread_opener,
    format_thread_reply,
)
from social.generate import (
    Take,
    generate_take,
    generate_takes,
    get_all_lenses,
    get_lens,
    pick_random_lens,
    pick_random_lenses,
)
from social.problems import pick_random_problem


def _get_posters(platform: str, config: SocialConfig) -> list:
    """Lazily import and instantiate platform posters."""
    posters = []

    if platform in ("x", "both"):
        if not config.has_x_credentials:
            click.echo(click.style("Warning: X credentials not configured, skipping X.", fg="yellow"))
        else:
            from social.platforms.x_poster import XPoster
            posters.append(XPoster(config))

    if platform in ("bluesky", "both"):
        if not config.has_bluesky_credentials:
            click.echo(click.style("Warning: Bluesky credentials not configured, skipping Bluesky.", fg="yellow"))
        else:
            from social.platforms.bluesky_poster import BlueskyPoster
            posters.append(BlueskyPoster(config))

    return posters


def _print_take(take: Take, config: SocialConfig, platform: str = "x") -> None:
    """Pretty-print a take and its formatted post."""
    click.echo(click.style(f"\n{'='*60}", fg="cyan"))
    click.echo(click.style(f"  {take.lens_emoji} {take.lens_name} (index {take.lens_index})", fg="cyan", bold=True))
    click.echo(click.style(f"{'='*60}", fg="cyan"))
    click.echo(click.style(f"\n  Headline: {take.headline}", bold=True))
    click.echo(f"  Body: {take.body}")

    formatted = format_single_post(take, app_link=config.app_link, platform=platform)
    click.echo(click.style(f"\n  --- Formatted for {platform.upper()} ({len(formatted)} chars) ---", fg="green"))
    for line in formatted.split("\n"):
        click.echo(f"  | {line}")
    click.echo()


@click.group()
def cli() -> None:
    """Endless Rumination Social Media Bot.

    Generate AI takes from 40 personas and post to X and Bluesky.
    """
    pass


@cli.command()
@click.option("--lens", type=int, default=None, help="Specific lens index (0-39)")
@click.option("--problem", type=str, default=None, help="Custom problem text")
@click.option("--platform", type=click.Choice(["x", "bluesky"]), default="x", help="Preview formatting for platform")
def preview(lens: Optional[int], problem: Optional[str], platform: str) -> None:
    """Generate a take and preview it — no posting."""
    config = load_config()

    if not config.anthropic_api_key:
        click.echo(click.style("Error: ANTHROPIC_API_KEY not set.", fg="red"))
        sys.exit(1)

    # Pick problem
    if problem is None:
        problem = pick_random_problem()
    click.echo(click.style(f"\n  Problem: \"{problem}\"", fg="yellow"))

    # Pick lens
    if lens is not None:
        try:
            lens_def = get_lens(lens)
        except ValueError:
            click.echo(click.style(f"Error: No lens with index {lens}.", fg="red"))
            sys.exit(1)
    else:
        lens_def = pick_random_lens()

    click.echo(click.style(f"  Generating take from {lens_def['emoji']} {lens_def['name']}...", fg="cyan"))

    take = generate_take(problem, lens_def, config)
    _print_take(take, config, platform)

    # Show cost estimate
    click.echo(click.style("  ~$0.006 (1 Sonnet call)", fg="bright_black"))


@cli.command()
@click.option("--platform", type=click.Choice(["x", "bluesky", "both"]), default="both", help="Target platform")
@click.option("--lens", type=int, default=None, help="Specific lens index (0-39)")
@click.option("--problem", type=str, default=None, help="Custom problem text")
@click.option("--dry-run", is_flag=True, help="Preview without posting")
def post(platform: str, lens: Optional[int], problem: Optional[str], dry_run: bool) -> None:
    """Generate and post a single take."""
    config = load_config()

    if not config.anthropic_api_key:
        click.echo(click.style("Error: ANTHROPIC_API_KEY not set.", fg="red"))
        sys.exit(1)

    # Pick problem
    if problem is None:
        problem = pick_random_problem()
    click.echo(click.style(f"\n  Problem: \"{problem}\"", fg="yellow"))

    # Pick lens
    if lens is not None:
        try:
            lens_def = get_lens(lens)
        except ValueError:
            click.echo(click.style(f"Error: No lens with index {lens}.", fg="red"))
            sys.exit(1)
    else:
        lens_def = pick_random_lens()

    click.echo(click.style(f"  Generating take from {lens_def['emoji']} {lens_def['name']}...", fg="cyan"))

    take = generate_take(problem, lens_def, config)

    if dry_run:
        click.echo(click.style("\n  [DRY RUN — not posting]", fg="yellow", bold=True))
        _print_take(take, config, platform if platform != "both" else "x")
        return

    # Post to platforms
    posters = _get_posters(platform, config)
    if not posters:
        click.echo(click.style("Error: No platform credentials configured.", fg="red"))
        sys.exit(1)

    for poster in posters:
        formatted = format_single_post(
            take,
            app_link=config.app_link,
            platform="bluesky" if poster.platform_name == "Bluesky" else "x",
        )
        click.echo(click.style(f"\n  Posting to {poster.platform_name}...", fg="cyan"))
        try:
            url = poster.post(formatted)
            click.echo(click.style(f"  Posted: {url}", fg="green", bold=True))
        except Exception as e:
            click.echo(click.style(f"  Failed to post to {poster.platform_name}: {e}", fg="red"))


@cli.command()
@click.option("--platform", type=click.Choice(["x", "bluesky", "both"]), default="both", help="Target platform")
@click.option("--problem", type=str, default=None, help="Custom problem text")
@click.option("--count", type=int, default=3, help="Number of takes in thread (2-5)")
@click.option("--dry-run", is_flag=True, help="Preview without posting")
def thread(platform: str, problem: Optional[str], count: int, dry_run: bool) -> None:
    """Generate and post a multi-take thread on one problem."""
    config = load_config()

    if not config.anthropic_api_key:
        click.echo(click.style("Error: ANTHROPIC_API_KEY not set.", fg="red"))
        sys.exit(1)

    count = max(2, min(5, count))

    # Pick problem
    if problem is None:
        problem = pick_random_problem()
    click.echo(click.style(f"\n  Problem: \"{problem}\"", fg="yellow"))

    # Pick lenses
    lenses = pick_random_lenses(count)
    lens_names = [f"{l['emoji']} {l['name']}" for l in lenses]
    click.echo(click.style(f"  Lenses: {', '.join(lens_names)}", fg="cyan"))
    click.echo(click.style(f"  Generating {count} takes...", fg="cyan"))

    takes = generate_takes(problem, lenses, config)

    # Build thread posts
    target_platform = platform if platform != "both" else "x"
    opener = format_thread_opener(
        problem,
        [l["name"] for l in lenses],
        platform=target_platform,
    )
    replies = [
        format_thread_reply(take, i + 1, len(takes), platform=target_platform)
        for i, take in enumerate(takes)
    ]
    thread_posts = [opener] + replies

    # Preview
    click.echo(click.style(f"\n  --- Thread Preview ({len(thread_posts)} posts) ---", fg="green"))
    for i, post_text in enumerate(thread_posts):
        label = "OPENER" if i == 0 else f"REPLY {i}/{len(takes)}"
        click.echo(click.style(f"\n  [{label}] ({len(post_text)} chars)", fg="green", bold=True))
        for line in post_text.split("\n"):
            click.echo(f"  | {line}")

    if dry_run:
        click.echo(click.style("\n  [DRY RUN — not posting]", fg="yellow", bold=True))
        cost = count * 0.006
        click.echo(click.style(f"  ~${cost:.3f} ({count} Sonnet calls)", fg="bright_black"))
        return

    # Post to platforms
    posters = _get_posters(platform, config)
    if not posters:
        click.echo(click.style("Error: No platform credentials configured.", fg="red"))
        sys.exit(1)

    for poster in posters:
        click.echo(click.style(f"\n  Posting thread to {poster.platform_name}...", fg="cyan"))
        try:
            urls = poster.thread(thread_posts)
            click.echo(click.style(f"  Thread posted ({len(urls)} posts):", fg="green", bold=True))
            for url in urls:
                click.echo(f"    {url}")
        except Exception as e:
            click.echo(click.style(f"  Failed to post thread to {poster.platform_name}: {e}", fg="red"))


@cli.command()
@click.option("--platform", type=click.Choice(["x", "bluesky", "both"]), default="both", help="Target platform")
@click.option("--version", required=True, help="Version string (e.g., 0.3.0)")
@click.option("--notes", required=True, help="What's new text")
@click.option("--dry-run", is_flag=True, help="Preview without posting")
def announce(platform: str, version: str, notes: str, dry_run: bool) -> None:
    """Post a version announcement."""
    config = load_config()

    target_platform = platform if platform != "both" else "x"
    formatted = format_announcement(
        version=version,
        notes=notes,
        app_link=config.app_link,
        platform=target_platform,
    )

    click.echo(click.style(f"\n  --- Announcement Preview ({len(formatted)} chars) ---", fg="green"))
    for line in formatted.split("\n"):
        click.echo(f"  | {line}")

    if dry_run:
        click.echo(click.style("\n  [DRY RUN — not posting]", fg="yellow", bold=True))
        return

    # Post to platforms
    posters = _get_posters(platform, config)
    if not posters:
        click.echo(click.style("Error: No platform credentials configured.", fg="red"))
        sys.exit(1)

    for poster in posters:
        click.echo(click.style(f"\n  Posting announcement to {poster.platform_name}...", fg="cyan"))
        try:
            url = poster.post(formatted)
            click.echo(click.style(f"  Posted: {url}", fg="green", bold=True))
        except Exception as e:
            click.echo(click.style(f"  Failed to post to {poster.platform_name}: {e}", fg="red"))
