from __future__ import annotations

from abc import ABC, abstractmethod


class TokenService(ABC):
    """Application port for issuing/invalidating JWT tokens."""

    @abstractmethod
    def generate_tokens(self, user_id: int) -> tuple[str, str]:
        """Return (access, refresh)."""

    @abstractmethod
    def blacklist_refresh(self, refresh: str) -> None: ...
