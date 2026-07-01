from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class CategoryNameResolver(ABC):
    """Port para resolver el nombre de una categoría por id."""

    @abstractmethod
    def find_name_by_id_and_owner(
        self, owner_id: int, category_id: int
    ) -> Optional[str]: ...