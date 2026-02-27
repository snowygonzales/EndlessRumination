"""X (Twitter) poster — uses tweepy for API v2 OAuth 1.0a."""
from __future__ import annotations

from typing import List

import tweepy

from social.config import SocialConfig
from social.platforms.base import BasePoster


class XPoster(BasePoster):
    """Post to X (Twitter) using API v2 with OAuth 1.0a User Authentication."""

    def __init__(self, config: SocialConfig) -> None:
        self._config = config
        self._client = tweepy.Client(
            consumer_key=config.x_api_key,
            consumer_secret=config.x_api_secret,
            access_token=config.x_access_token,
            access_token_secret=config.x_access_token_secret,
        )

    def post(self, text: str) -> str:
        """Post a single tweet. Returns the tweet URL."""
        response = self._client.create_tweet(text=text)
        tweet_id = response.data["id"]
        return f"https://x.com/i/status/{tweet_id}"

    def thread(self, posts: List[str]) -> List[str]:
        """Post a thread — each post replies to the previous one."""
        urls: list[str] = []
        reply_to = None

        for text in posts:
            response = self._client.create_tweet(
                text=text,
                in_reply_to_tweet_id=reply_to,
            )
            tweet_id = response.data["id"]
            reply_to = tweet_id
            urls.append(f"https://x.com/i/status/{tweet_id}")

        return urls

    def verify_credentials(self) -> bool:
        """Verify X API credentials by fetching the authenticated user."""
        try:
            me = self._client.get_me()
            return me.data is not None
        except Exception:
            return False

    @property
    def platform_name(self) -> str:
        return "X"
