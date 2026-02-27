"""Bluesky poster — uses atproto (AT Protocol) with app password auth."""
from __future__ import annotations

from typing import List

from atproto import Client as BSClient
from atproto import models as bsky_models

from social.config import SocialConfig
from social.platforms.base import BasePoster


class BlueskyPoster(BasePoster):
    """Post to Bluesky using the AT Protocol."""

    def __init__(self, config: SocialConfig) -> None:
        self._config = config
        self._client = BSClient()
        self._client.login(config.bluesky_handle, config.bluesky_app_password)

    def post(self, text: str) -> str:
        """Post a single skeet. Returns the post URL."""
        response = self._client.send_post(text=text)
        return self._uri_to_url(response.uri)

    def thread(self, posts: List[str]) -> List[str]:
        """Post a thread — each post replies to the previous one."""
        urls: list[str] = []
        parent_ref = None
        root_ref = None

        for text in posts:
            reply_to = None
            if parent_ref is not None:
                reply_to = bsky_models.AppBskyFeedPost.ReplyRef(
                    parent=parent_ref,
                    root=root_ref,
                )

            response = self._client.send_post(text=text, reply_to=reply_to)
            ref = bsky_models.create_strong_ref(response)

            if root_ref is None:
                root_ref = ref
            parent_ref = ref

            urls.append(self._uri_to_url(response.uri))

        return urls

    def verify_credentials(self) -> bool:
        """Verify Bluesky credentials by checking the profile."""
        try:
            profile = self._client.get_profile(self._config.bluesky_handle)
            return profile is not None
        except Exception:
            return False

    @property
    def platform_name(self) -> str:
        return "Bluesky"

    def _uri_to_url(self, uri: str) -> str:
        """Convert an AT URI to a web URL.

        AT URI format: at://did:plc:xxxx/app.bsky.feed.post/rkey
        Web URL format: https://bsky.app/profile/{handle}/post/{rkey}
        """
        parts = uri.split("/")
        rkey = parts[-1]
        return f"https://bsky.app/profile/{self._config.bluesky_handle}/post/{rkey}"
