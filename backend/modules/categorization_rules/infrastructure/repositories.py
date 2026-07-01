from __future__ import annotations

from typing import Optional

from modules.categorization_rules.domain.entities import CategorizationRule
from modules.categorization_rules.domain.repositories import (
    CategorizationRuleRepository,
)

from modules.categorization_rules.infrastructure.models import (
    CategorizationRule as CategorizationRuleORM,
)


class DjangoCategorizationRuleRepository(CategorizationRuleRepository):
    def save(
        self,
        owner_id: int,
        pattern: str,
        match_type: str,
        category_id: int,
        kind: str,
        priority: int,
    ) -> CategorizationRule:
        orm = CategorizationRuleORM.objects.create(
            owner_id=owner_id,
            pattern=pattern,
            match_type=match_type,
            category_id=category_id,
            kind=kind,
            priority=priority,
        )
        return self._to_entity(orm)

    def find_by_id(self, rule_id: int) -> Optional[CategorizationRule]:
        try:
            orm = CategorizationRuleORM.objects.get(pk=rule_id)
        except CategorizationRuleORM.DoesNotExist:
            return None
        return self._to_entity(orm)

    def list_by_owner(self, owner_id: int) -> list[CategorizationRule]:
        qs = CategorizationRuleORM.objects.filter(owner_id=owner_id).order_by(
            "-priority", "-created_at"
        )
        return [self._to_entity(o) for o in qs]

    def list_active_by_owner(self, owner_id: int) -> list[CategorizationRule]:
        qs = CategorizationRuleORM.objects.filter(
            owner_id=owner_id, is_active=True
        ).order_by("-priority", "-created_at")
        return [self._to_entity(o) for o in qs]

    def update(
        self,
        rule_id: int,
        pattern: Optional[str] = None,
        match_type: Optional[str] = None,
        category_id: Optional[int] = None,
        kind: Optional[str] = None,
        priority: Optional[int] = None,
    ) -> CategorizationRule:
        fields: dict[str, object] = {}
        if pattern is not None:
            fields["pattern"] = pattern
        if match_type is not None:
            fields["match_type"] = match_type
        if category_id is not None:
            fields["category_id"] = category_id
        if kind is not None:
            fields["kind"] = kind
        if priority is not None:
            fields["priority"] = priority

        if fields:
            CategorizationRuleORM.objects.filter(pk=rule_id).update(**fields)

        return self.find_by_id(rule_id)  # type: ignore[return-value]

    def deactivate(self, rule_id: int) -> CategorizationRule:
        CategorizationRuleORM.objects.filter(pk=rule_id).update(is_active=False)
        return self.find_by_id(rule_id)  # type: ignore[return-value]

    def activate(self, rule_id: int) -> CategorizationRule:
        CategorizationRuleORM.objects.filter(pk=rule_id).update(is_active=True)
        return self.find_by_id(rule_id)  # type: ignore[return-value]

    def delete(self, rule_id: int) -> None:
        CategorizationRuleORM.objects.filter(pk=rule_id).delete()

    def exists_active_duplicate_for_owner(
        self,
        owner_id: int,
        pattern: str,
        match_type: str,
        exclude_id: Optional[int] = None,
    ) -> bool:
        qs = CategorizationRuleORM.objects.filter(
            owner_id=owner_id,
            pattern=pattern,
            match_type=match_type,
            is_active=True,
        )
        if exclude_id is not None:
            qs = qs.exclude(pk=exclude_id)
        return qs.exists()

    @staticmethod
    def _to_entity(orm: CategorizationRuleORM) -> CategorizationRule:
        return CategorizationRule(
            id=orm.id,
            owner_id=orm.owner_id,
            pattern=orm.pattern,
            match_type=orm.match_type,
            category_id=orm.category_id,
            kind=orm.kind,
            priority=orm.priority,
            is_active=orm.is_active,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )