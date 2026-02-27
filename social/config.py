"""Configuration loader — reads env vars from social/.env, falls back to backend/.env."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Resolve paths relative to this file
_SOCIAL_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SOCIAL_DIR.parent
_BACKEND_ENV = _PROJECT_ROOT / "backend" / ".env"
_SOCIAL_ENV = _SOCIAL_DIR / ".env"


def _load_env() -> None:
    """Load .env files — social/.env takes precedence, backend/.env as fallback.

    Both are loaded with override=True so they always set env vars, even if
    the shell already has empty values. Social .env is loaded second so its
    values win over backend .env for any shared keys.
    """
    if _BACKEND_ENV.exists():
        load_dotenv(str(_BACKEND_ENV), override=True)
    if _SOCIAL_ENV.exists():
        load_dotenv(str(_SOCIAL_ENV), override=True)


@dataclass
class SocialConfig:
    """All configuration for the social media bot."""

    # Anthropic
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"
    claude_max_tokens: int = 400

    # X (Twitter) API v2
    x_api_key: str = ""
    x_api_secret: str = ""
    x_access_token: str = ""
    x_access_token_secret: str = ""

    # Bluesky
    bluesky_handle: str = ""
    bluesky_app_password: str = ""

    # App links
    app_store_url: str = ""
    play_store_url: str = ""
    website_url: str = "https://github.com/snowygonzales/EndlessRumination"

    @property
    def has_x_credentials(self) -> bool:
        return all([self.x_api_key, self.x_api_secret, self.x_access_token, self.x_access_token_secret])

    @property
    def has_bluesky_credentials(self) -> bool:
        return all([self.bluesky_handle, self.bluesky_app_password])

    @property
    def app_link(self) -> str:
        """Return the best available app link."""
        return self.app_store_url or self.play_store_url or self.website_url


def load_config() -> SocialConfig:
    """Load configuration from environment variables."""
    _load_env()

    return SocialConfig(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        claude_model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
        claude_max_tokens=int(os.getenv("CLAUDE_MAX_TOKENS", "400")),
        x_api_key=os.getenv("X_API_KEY", ""),
        x_api_secret=os.getenv("X_API_SECRET", ""),
        x_access_token=os.getenv("X_ACCESS_TOKEN", ""),
        x_access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET", ""),
        bluesky_handle=os.getenv("BLUESKY_HANDLE", ""),
        bluesky_app_password=os.getenv("BLUESKY_APP_PASSWORD", ""),
        app_store_url=os.getenv("APP_STORE_URL", ""),
        play_store_url=os.getenv("PLAY_STORE_URL", ""),
        website_url=os.getenv("WEBSITE_URL", "https://github.com/snowygonzales/EndlessRumination"),
    )
