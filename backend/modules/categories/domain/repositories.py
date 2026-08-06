from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .entities import Category


class CategoryRepository(ABC):
    """Domain port for category persistence. Implemented by infrastructure."""

    @abstractmethod
    def save(
        self,
        owner_id: int,
        name: str,
        kind: str,
        include_in_summaries: bool = True,
        is_fixed: bool = False,
    ) -> Category: ...

    @abstractmethod
    def find_by_id(self, category_id: int) -> Optional[Category]: ...

    @abstractmethod
    def list_by_owner(self, owner_id: int) -> list[Category]: ...

    @abstractmethod
    def update(
        self,
        category_id: int,
        name: Optional[str] = None,
        kind: Optional[str] = None,
        include_in_summaries: Optional[bool] = None,
        is_fixed: Optional[bool] = None,
    ) -> Category: ...

    @abstractmethod
    def deactivate(self, category_id: int) -> Category: ...

    @abstractmethod
    def activate(self, category_id: int) -> Category: ...

    @abstractmethod
    def exists_active_name_for_owner(self, owner_id: int, name: str) -> bool: ...