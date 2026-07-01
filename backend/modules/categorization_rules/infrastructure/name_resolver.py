from __future__ import annotations

from typing import Optional

from modules.categorization_rules.application.ports import CategoryNameResolver
from modules.categories.domain.repositories import CategoryRepository


class CategoryRepositoryNameResolver(CategoryNameResolver):
    """Adapta CategoryRepository al port CategoryNameResolver."""

    def __init__(self, category_repository: CategoryRepository) -> None:
        self._category_repository = category_repository

    def find_name_by_id_and_owner(
        self, owner_id: int, category_id: int
    ) -> Optional[str]:
        category = self._category_repository.find_by_id(category_id)
        if category is None or category.owner_id != owner_id:
            return None
        return category.name