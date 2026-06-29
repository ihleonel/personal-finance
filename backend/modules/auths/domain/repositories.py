from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .entities import User


class UserRepository(ABC):
    """Domain port for user persistence. Implemented by infrastructure."""

    @abstractmethod
    def exists_by_email(self, email: str) -> bool: ...

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]: ...

    @abstractmethod
    def find_by_id(self, user_id: int) -> Optional[User]: ...

    @abstractmethod
    def save(
        self,
        email: str,
        password_hash: str,
        first_name: str = "",
        last_name: str = "",
        is_active: bool = True,
    ) -> User: ...

    @abstractmethod
    def update(
        self,
        user_id: int,
        first_name: str = "",
        last_name: str = "",
    ) -> User: ...

    @abstractmethod
    def get_password_hash(self, email: str) -> Optional[str]: ...

    @abstractmethod
    def update_password(self, user_id: int, password_hash: str) -> None: ...
