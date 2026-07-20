from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from django.db import transaction as db_transaction

from modules.shared.domain.optional import UNSET
from modules.shared.domain.text_utils import normalize_description
from modules.transactions.domain.entities import Transaction
from modules.transactions.domain.repositories import (
    BulkAssignCategoryResult,
    TransactionRepository,
)
from modules.transactions.models import Transaction as TransactionORM


class DjangoTransactionRepository(TransactionRepository):
    def save(
        self,
        owner_id: int,
        account_id: int,
        category_id: Optional[int],
        kind: str,
        amount: Decimal,
        date: date,
        description: str,
        source: str = "",
        external_reference: str = "",
    ) -> Transaction:
        orm = TransactionORM.objects.create(
            owner_id=owner_id,
            account_id=account_id,
            category_id=category_id,
            kind=kind,
            amount=amount,
            date=date,
            description=description,
            source=source,
            external_reference=external_reference,
        )
        return self._to_entity(orm)

    def find_existing(
        self,
        owner_id: int,
        account_id: int,
        source: str,
        external_reference: str,
        date: date,
        amount: Decimal,
        description: str,
    ) -> Optional[Transaction]:
        if not source or not external_reference:
            return None
        orm = (
            TransactionORM.objects
            .filter(
                owner_id=owner_id,
                account_id=account_id,
                source=source,
                external_reference=external_reference,
                date=date,
                amount=amount,
                description=description,
            )
            .first()
        )
        return self._to_entity(orm) if orm is not None else None

    def find_by_id(self, transaction_id: int) -> Optional[Transaction]:
        try:
            orm = TransactionORM.objects.get(pk=transaction_id)
        except TransactionORM.DoesNotExist:
            return None
        return self._to_entity(orm)

    def list_by_owner(
        self,
        owner_id: int,
        account_id: Optional[int] = None,
        kind: Optional[str] = None,
        category_id: Optional[int] = None,
        category_id_isnull: bool = False,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        description: Optional[str] = None,
    ) -> list[Transaction]:
        qs = TransactionORM.objects.filter(owner_id=owner_id)
        if account_id is not None:
            qs = qs.filter(account_id=account_id)
        if kind is not None:
            qs = qs.filter(kind=kind)
        if category_id_isnull:
            qs = qs.filter(category_id__isnull=True)
        elif category_id is not None:
            qs = qs.filter(category_id=category_id)
        if date_from is not None:
            qs = qs.filter(date__gte=date_from)
        if date_to is not None:
            qs = qs.filter(date__lte=date_to)
        qs = qs.order_by("-date", "-created_at")
        entities = [self._to_entity(o) for o in qs]
        if description:
            needle = normalize_description(description)
            if needle:
                entities = [
                    t for t in entities if needle in normalize_description(t.description or "")
                ]
        return entities

    def update(
        self,
        transaction_id: int,
        amount: Optional[Decimal] = None,
        date: Optional[date] = None,
        description: Optional[str] = None,
        category_id: object = UNSET,
    ) -> Transaction:
        fields: dict[str, object] = {}
        if amount is not None:
            fields["amount"] = amount
        if date is not None:
            fields["date"] = date
        if description is not None:
            fields["description"] = description
        if category_id is not UNSET:
            fields["category_id"] = category_id

        if fields:
            TransactionORM.objects.filter(pk=transaction_id).update(**fields)

        return self.find_by_id(transaction_id)  # type: ignore[return-value]

    def delete(self, transaction_id: int) -> None:
        TransactionORM.objects.filter(pk=transaction_id).delete()

    def bulk_assign_category(
        self,
        owner_id: int,
        transaction_ids: list[int],
        category_id: Optional[int],
        expected_kind: Optional[str],
    ) -> BulkAssignCategoryResult:
        with db_transaction.atomic():
            qs = TransactionORM.objects.filter(
                owner_id=owner_id, pk__in=transaction_ids
            )
            if expected_kind is not None:
                mismatched = list(
                    qs.exclude(kind=expected_kind)
                    .values_list("pk", flat=True)
                )
            else:
                mismatched = []

            target = qs
            if expected_kind is not None:
                target = target.filter(kind=expected_kind)
            updated_count = target.update(category_id=category_id)

            found_ids = set(qs.values_list("pk", flat=True))
            skipped_ids = [tid for tid in transaction_ids if tid not in found_ids]
            return BulkAssignCategoryResult(
                updated_count=updated_count,
                skipped_ids=skipped_ids,
                skipped_kinds=mismatched,
            )

    @staticmethod
    def _to_entity(orm: TransactionORM) -> Transaction:
        return Transaction(
            id=orm.id,
            owner_id=orm.owner_id,
            account_id=orm.account_id,
            category_id=orm.category_id,
            kind=orm.kind,
            amount=orm.amount,
            date=orm.date,
            description=orm.description,
            source=orm.source,
            external_reference=orm.external_reference,
            created_at=orm.created_at,
        )