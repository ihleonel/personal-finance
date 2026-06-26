"""Shared fakes for testing application use_cases without Django ORM / DRF.

These fakes implement the domain ports (UserRepository, TokenService) so that
the application layer can be tested in isolation.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Optional

from modules.auths.application.ports import TokenService
from modules.auths.domain.entities import User


@dataclass
class InMemoryUserRepository:
    """Implements modules.auths.domain.repositories.UserRepository in memory."""

    _by_email: dict[str, tuple[User, str]] = field(default_factory=dict)
    _by_id: dict[int, tuple[User, str]] = field(default_factory=dict)
    _next_id: int = field(default=1)

    def exists_by_email(self, email: str) -> bool:
        return email.lower() in self._by_email

    def find_by_email(self, email: str) -> Optional[User]:
        return self._by_email.get(email.lower(), (None, None))[0]

    def find_by_id(self, user_id: int) -> Optional[User]:
        return self._by_id.get(user_id, (None, None))[0]

    def save(
        self,
        email: str,
        password_hash: str,
        first_name: str = "",
        last_name: str = "",
        is_active: bool = True,
    ) -> User:
        user_id = self._next_id
        self._next_id += 1
        user = User(
            id=user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
        )
        self._by_email[email.lower()] = (user, password_hash)
        self._by_id[user_id] = (user, password_hash)
        return user

    def get_password_hash(self, email: str) -> Optional[str]:
        return self._by_email.get(email.lower(), (None, None))[1]

    def update(
        self,
        user_id: int,
        first_name: str = "",
        last_name: str = "",
    ) -> User:
        user, password_hash = self._by_id[user_id]
        if first_name:
            user = replace(user, first_name=first_name)
        if last_name:
            user = replace(user, last_name=last_name)
        self._by_id[user_id] = (user, password_hash)
        self._by_email[user.email.lower()] = (user, password_hash)
        return user

    def seed(
        self,
        email: str,
        password_hash: str,
        first_name: str = "",
        last_name: str = "",
        is_active: bool = True,
    ) -> User:
        return self.save(email, password_hash, first_name, last_name, is_active)


@dataclass
class FakeTokenService:
    """Implements modules.auths.application.ports.TokenService."""

    access_prefix: str = "fake-access"
    refresh_prefix: str = "fake-refresh"
    blacklisted: list[str] = field(default_factory=list)
    generated: list[int] = field(default_factory=list)

    def generate_tokens(self, user_id: int) -> tuple[str, str]:
        self.generated.append(user_id)
        return f"{self.access_prefix}-{user_id}", f"{self.refresh_prefix}-{user_id}"

    def blacklist_refresh(self, refresh: str) -> None:
        self.blacklisted.append(refresh)
