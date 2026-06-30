from __future__ import annotations

from typing import Optional

from modules.categories.domain.entities import Category
from modules.categories.domain.repositories import CategoryRepository

from modules.categories.models import Category as CategoryORM


class DjangoCategoryRepository(CategoryRepository):
    def save(self, owner_id: int, name: str, kind: str) -> Category:
        orm = CategoryORM.objects.create(
            owner_id=owner_id,
            name=name,
            kind=kind,
        )
        return self._to_entity(orm)

    def find_by_id(self, category_id: int) -> Optional[Category]:
        try:
            orm = CategoryORM.objects.get(pk=category_id)
        except CategoryORM.DoesNotExist:
            return None
        return self._to_entity(orm)

    def list_by_owner(self, owner_id: int) -> list[Category]:
        qs = CategoryORM.objects.filter(owner_id=owner_id).order_by("-created_at")
        return [self._to_entity(o) for o in qs]

    def update(
        self,
        category_id: int,
        name: Optional[str] = None,
        kind: Optional[str] = None,
    ) -> Category:
        fields: dict[str, object] = {}
        if name is not None:
            fields["name"] = name
        if kind is not None:
            fields["kind"] = kind

        if fields:
            CategoryORM.objects.filter(pk=category_id).update(**fields)

        return self.find_by_id(category_id)  # type: ignore[return-value]

    def deactivate(self, category_id: int) -> Category:
        CategoryORM.objects.filter(pk=category_id).update(is_active=False)
        return self.find_by_id(category_id)  # type: ignore[return-value]

    def activate(self, category_id: int) -> Category:
        CategoryORM.objects.filter(pk=category_id).update(is_active=True)
        return self.find_by_id(category_id)  # type: ignore[return-value]

    def exists_active_name_for_owner(self, owner_id: int, name: str) -> bool:
        return CategoryORM.objects.filter(
            owner_id=owner_id, name=name, is_active=True
        ).exists()

    @staticmethod
    def _to_entity(orm: CategoryORM) -> Category:
        return Category(
            id=orm.id,
            owner_id=orm.owner_id,
            name=orm.name,
            kind=orm.kind,
            is_active=orm.is_active,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )