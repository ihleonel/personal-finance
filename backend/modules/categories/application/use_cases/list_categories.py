from __future__ import annotations

from dataclasses import dataclass

from modules.categories.application.dtos import CategoryOutput
from modules.categories.domain.repositories import CategoryRepository
from modules.shared.application.result import Result


@dataclass
class ListCategoriesUseCase:
    repository: CategoryRepository

    def execute(self, owner_id: int) -> Result[list[CategoryOutput]]:
        categories = self.repository.list_by_owner(owner_id)
        outputs = [
            CategoryOutput(
                id=c.id or 0,
                owner_id=c.owner_id,
                name=c.name,
                kind=c.kind,
                is_active=c.is_active,
            )
            for c in categories
        ]
        return Result.ok(outputs)