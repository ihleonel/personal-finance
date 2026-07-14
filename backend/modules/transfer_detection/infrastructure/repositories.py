from __future__ import annotations

from typing import Optional

from modules.transfer_detection.domain.entities import TransferDetectionRule
from modules.transfer_detection.domain.repositories import (
    TransferDetectionRuleRepository,
)
from modules.transfer_detection.infrastructure.models import (
    TransferDetectionRule as TransferDetectionRuleORM,
)


class DjangoTransferDetectionRuleRepository(TransferDetectionRuleRepository):
    def save(
        self,
        owner_id: int,
        pattern: str,
        match_type: str,
        priority: int,
    ) -> TransferDetectionRule:
        orm = TransferDetectionRuleORM.objects.create(
            owner_id=owner_id,
            pattern=pattern,
            match_type=match_type,
            priority=priority,
        )
        return self._to_entity(orm)

    def find_by_id(self, rule_id: int) -> Optional[TransferDetectionRule]:
        try:
            orm = TransferDetectionRuleORM.objects.get(pk=rule_id)
        except TransferDetectionRuleORM.DoesNotExist:
            return None
        return self._to_entity(orm)

    def list_by_owner(self, owner_id: int) -> list[TransferDetectionRule]:
        qs = TransferDetectionRuleORM.objects.filter(owner_id=owner_id).order_by(
            "-priority", "-created_at"
        )
        return [self._to_entity(o) for o in qs]

    def list_active_by_owner(self, owner_id: int) -> list[TransferDetectionRule]:
        qs = TransferDetectionRuleORM.objects.filter(
            owner_id=owner_id, is_active=True
        ).order_by("-priority", "-created_at")
        return [self._to_entity(o) for o in qs]

    def update(
        self,
        rule_id: int,
        pattern: Optional[str] = None,
        match_type: Optional[str] = None,
        priority: Optional[int] = None,
    ) -> TransferDetectionRule:
        fields: dict[str, object] = {}
        if pattern is not None:
            fields["pattern"] = pattern
        if match_type is not None:
            fields["match_type"] = match_type
        if priority is not None:
            fields["priority"] = priority

        if fields:
            TransferDetectionRuleORM.objects.filter(pk=rule_id).update(**fields)

        return self.find_by_id(rule_id)  # type: ignore[return-value]

    def deactivate(self, rule_id: int) -> TransferDetectionRule:
        TransferDetectionRuleORM.objects.filter(pk=rule_id).update(is_active=False)
        return self.find_by_id(rule_id)  # type: ignore[return-value]

    def activate(self, rule_id: int) -> TransferDetectionRule:
        TransferDetectionRuleORM.objects.filter(pk=rule_id).update(is_active=True)
        return self.find_by_id(rule_id)  # type: ignore[return-value]

    def delete(self, rule_id: int) -> None:
        TransferDetectionRuleORM.objects.filter(pk=rule_id).delete()

    def exists_active_duplicate_for_owner(
        self,
        owner_id: int,
        pattern: str,
        match_type: str,
        exclude_id: Optional[int] = None,
    ) -> bool:
        qs = TransferDetectionRuleORM.objects.filter(
            owner_id=owner_id,
            pattern=pattern,
            match_type=match_type,
            is_active=True,
        )
        if exclude_id is not None:
            qs = qs.exclude(pk=exclude_id)
        return qs.exists()

    @staticmethod
    def _to_entity(orm: TransferDetectionRuleORM) -> TransferDetectionRule:
        return TransferDetectionRule(
            id=orm.id,
            owner_id=orm.owner_id,
            pattern=orm.pattern,
            match_type=orm.match_type,
            priority=orm.priority,
            is_active=orm.is_active,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )