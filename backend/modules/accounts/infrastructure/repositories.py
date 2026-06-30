from __future__ import annotations

from decimal import Decimal
from typing import Optional

from modules.accounts.domain.entities import Account
from modules.accounts.domain.repositories import AccountRepository

from modules.accounts.models import Account as AccountORM


class DjangoAccountRepository(AccountRepository):
    def save(
        self,
        owner_id: int,
        name: str,
        account_type: str,
        currency: str,
        initial_balance: Decimal,
    ) -> Account:
        orm = AccountORM.objects.create(
            owner_id=owner_id,
            name=name,
            account_type=account_type,
            currency=currency,
            initial_balance=initial_balance,
        )
        return self._to_entity(orm)

    def find_by_id(self, account_id: int) -> Optional[Account]:
        try:
            orm = AccountORM.objects.get(pk=account_id)
        except AccountORM.DoesNotExist:
            return None
        return self._to_entity(orm)

    def list_by_owner(self, owner_id: int) -> list[Account]:
        qs = AccountORM.objects.filter(owner_id=owner_id).order_by("-created_at")
        return [self._to_entity(o) for o in qs]

    def update(
        self,
        account_id: int,
        name: Optional[str] = None,
        account_type: Optional[str] = None,
        currency: Optional[str] = None,
        initial_balance: Optional[Decimal] = None,
    ) -> Account:
        fields: dict[str, object] = {}
        if name is not None:
            fields["name"] = name
        if account_type is not None:
            fields["account_type"] = account_type
        if currency is not None:
            fields["currency"] = currency
        if initial_balance is not None:
            fields["initial_balance"] = initial_balance

        if fields:
            AccountORM.objects.filter(pk=account_id).update(**fields)

        return self.find_by_id(account_id)  # type: ignore[return-value]

    def deactivate(self, account_id: int) -> Account:
        AccountORM.objects.filter(pk=account_id).update(is_active=False)
        return self.find_by_id(account_id)  # type: ignore[return-value]

    def activate(self, account_id: int) -> Account:
        AccountORM.objects.filter(pk=account_id).update(is_active=True)
        return self.find_by_id(account_id)  # type: ignore[return-value]

    def exists_active_name_for_owner(self, owner_id: int, name: str) -> bool:
        return AccountORM.objects.filter(
            owner_id=owner_id, name=name, is_active=True
        ).exists()

    @staticmethod
    def _to_entity(orm: AccountORM) -> Account:
        return Account(
            id=orm.id,
            owner_id=orm.owner_id,
            name=orm.name,
            account_type=orm.account_type,
            currency=orm.currency,
            initial_balance=orm.initial_balance,
            is_active=orm.is_active,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )