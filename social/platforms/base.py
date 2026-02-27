"""Abstract base class for social media platform posters."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


class BasePoster(ABC):
    """Interface for posting to a social media platform."""

    @abstractmethod
    def post(self, text: str) -> str:
        """Post a single message.

        Args:
            text: The formatted post text.

        Returns:
            The URL of the created post.
        """
        ...

    @abstractmethod
    def thread(self, posts: List[str]) -> List[str]:
        """Post a thread (list of messages in reply chain).

        Args:
            posts: Ordered list of post texts. First is the opener.

        Returns:
            List of URLs for each post in the thread.
        """
        ...

    @abstractmethod
    def verify_credentials(self) -> bool:
        """Check if the configured credentials are valid.

        Returns:
            True if credentials are valid and can post.
        """
        ...

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Human-readable platform name (e.g., 'X', 'Bluesky')."""
        ...
