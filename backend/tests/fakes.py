"""Shared fakes for testing application use_cases without Django ORM / DRF.

These fakes implement the domain ports (UserRepository, TokenService) so that
the application layer can be tested in isolation.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from modules.accounts.domain.entities import Account
from modules.accounts.domain.repositories import AccountRepository
from modules.auths.application.ports import TokenService
from modules.auths.domain.entities import User
from modules.categories.domain.entities import Category
from modules.categories.domain.repositories import CategoryRepository
from modules.categorization_rules.application.ports import CategoryNameResolver
from modules.categorization_rules.domain.entities import CategorizationRule
from modules.categorization_rules.domain.repositories import (
    CategorizationRuleRepository,
)
from modules.shared.domain.optional import UNSET
from modules.transactions.domain.entities import Transaction
from modules.transactions.domain.repositories import TransactionRepository


@dataclass
class InMemoryUserRepository:
    """Implements modules.auths.domain.repositories.UserRepository in memory."""

    _by_email: dict[str, tuple[User, str]] = field(default_factory=dict)
    _by_id: dict[int, tuple[User, str]] = field(default_factory=dict)
    _next_id: int = field(default=1)

    def exists_by_email(self, email: str) -> bool:
        return email.lower() in self._by_email

    def find_by_email(self, email: str) -> Optional[User]:
        return self._by_email.get(email.lower(), (None, None))[0]

    def find_by_id(self, user_id: int) -> Optional[User]:
        return self._by_id.get(user_id, (None, None))[0]

    def save(
        self,
        email: str,
        password_hash: str,
        first_name: str = "",
        last_name: str = "",
        is_active: bool = True,
    ) -> User:
        user_id = self._next_id
        self._next_id += 1
        user = User(
            id=user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
        )
        self._by_email[email.lower()] = (user, password_hash)
        self._by_id[user_id] = (user, password_hash)
        return user

    def get_password_hash(self, email: str) -> Optional[str]:
        return self._by_email.get(email.lower(), (None, None))[1]

    def update(
        self,
        user_id: int,
        first_name: str = "",
        last_name: str = "",
    ) -> User:
        user, password_hash = self._by_id[user_id]
        if first_name:
            user = replace(user, first_name=first_name)
        if last_name:
            user = replace(user, last_name=last_name)
        self._by_id[user_id] = (user, password_hash)
        self._by_email[user.email.lower()] = (user, password_hash)
        return user

    def seed(
        self,
        email: str,
        password_hash: str,
        first_name: str = "",
        last_name: str = "",
        is_active: bool = True,
    ) -> User:
        return self.save(email, password_hash, first_name, last_name, is_active)

    def update_password(self, user_id: int, password_hash: str) -> None:
        user, _ = self._by_id[user_id]
        email_key = user.email.lower()
        _, _ = self._by_email[email_key]
        self._by_id[user_id] = (user, password_hash)
        self._by_email[email_key] = (user, password_hash)


@dataclass
class FakeTokenService:
    """Implements modules.auths.application.ports.TokenService."""

    access_prefix: str = "fake-access"
    refresh_prefix: str = "fake-refresh"
    blacklisted: list[str] = field(default_factory=list)
    generated: list[int] = field(default_factory=list)

    def generate_tokens(self, user_id: int) -> tuple[str, str]:
        self.generated.append(user_id)
        return f"{self.access_prefix}-{user_id}", f"{self.refresh_prefix}-{user_id}"

    def blacklist_refresh(self, refresh: str) -> None:
        self.blacklisted.append(refresh)


@dataclass
class InMemoryAccountRepository:
    """Implements modules.accounts.domain.repositories.AccountRepository in memory."""

    _by_id: dict[int, Account] = field(default_factory=dict)
    _next_id: int = field(default=1)

    def save(
        self,
        owner_id: int,
        name: str,
        account_type: str,
        currency: str,
        initial_balance: Decimal,
    ) -> Account:
        account_id = self._next_id
        self._next_id += 1
        account = Account(
            id=account_id,
            owner_id=owner_id,
            name=name,
            account_type=account_type,
            currency=currency,
            initial_balance=initial_balance.quantize(Decimal("0.01")),
            is_active=True,
        )
        self._by_id[account_id] = account
        return account

    def find_by_id(self, account_id: int) -> Optional[Account]:
        return self._by_id.get(account_id)

    def list_by_owner(self, owner_id: int) -> list[Account]:
        return [a for a in self._by_id.values() if a.owner_id == owner_id]

    def update(
        self,
        account_id: int,
        name: Optional[str] = None,
        account_type: Optional[str] = None,
        currency: Optional[str] = None,
        initial_balance: Optional[Decimal] = None,
    ) -> Account:
        current = self._by_id[account_id]
        updated = replace(
            current,
            name=name if name is not None else current.name,
            account_type=account_type if account_type is not None else current.account_type,
            currency=currency if currency is not None else current.currency,
            initial_balance=initial_balance.quantize(Decimal("0.01"))
            if initial_balance is not None
            else current.initial_balance,
        )
        self._by_id[account_id] = updated
        return updated

    def deactivate(self, account_id: int) -> Account:
        current = self._by_id[account_id]
        updated = replace(current, is_active=False)
        self._by_id[account_id] = updated
        return updated

    def activate(self, account_id: int) -> Account:
        current = self._by_id[account_id]
        updated = replace(current, is_active=True)
        self._by_id[account_id] = updated
        return updated

    def exists_active_name_for_owner(self, owner_id: int, name: str) -> bool:
        return any(
            a.owner_id == owner_id and a.name == name and a.is_active
            for a in self._by_id.values()
        )

    def seed(
        self,
        owner_id: int,
        name: str,
        account_type: str = "cash",
        currency: str = "ARS",
        initial_balance: Decimal = Decimal("0"),
        is_active: bool = True,
    ) -> Account:
        account_id = self._next_id
        self._next_id += 1
        account = Account(
            id=account_id,
            owner_id=owner_id,
            name=name,
            account_type=account_type,
            currency=currency,
            initial_balance=initial_balance.quantize(Decimal("0.01")),
            is_active=is_active,
        )
        self._by_id[account_id] = account
        return account


@dataclass
class InMemoryCategoryRepository:
    """Implements modules.categories.domain.repositories.CategoryRepository in memory."""

    _by_id: dict[int, Category] = field(default_factory=dict)
    _next_id: int = field(default=1)

    def save(self, owner_id: int, name: str, kind: str) -> Category:
        category_id = self._next_id
        self._next_id += 1
        category = Category(
            id=category_id,
            owner_id=owner_id,
            name=name,
            kind=kind,
            is_active=True,
        )
        self._by_id[category_id] = category
        return category

    def find_by_id(self, category_id: int) -> Optional[Category]:
        return self._by_id.get(category_id)

    def list_by_owner(self, owner_id: int) -> list[Category]:
        return [c for c in self._by_id.values() if c.owner_id == owner_id]

    def update(
        self,
        category_id: int,
        name: Optional[str] = None,
        kind: Optional[str] = None,
    ) -> Category:
        current = self._by_id[category_id]
        updated = replace(
            current,
            name=name if name is not None else current.name,
            kind=kind if kind is not None else current.kind,
        )
        self._by_id[category_id] = updated
        return updated

    def deactivate(self, category_id: int) -> Category:
        current = self._by_id[category_id]
        updated = replace(current, is_active=False)
        self._by_id[category_id] = updated
        return updated

    def activate(self, category_id: int) -> Category:
        current = self._by_id[category_id]
        updated = replace(current, is_active=True)
        self._by_id[category_id] = updated
        return updated

    def exists_active_name_for_owner(self, owner_id: int, name: str) -> bool:
        return any(
            c.owner_id == owner_id and c.name == name and c.is_active
            for c in self._by_id.values()
        )

    def seed(
        self,
        owner_id: int,
        name: str,
        kind: str = "expense",
        is_active: bool = True,
    ) -> Category:
        category_id = self._next_id
        self._next_id += 1
        category = Category(
            id=category_id,
            owner_id=owner_id,
            name=name,
            kind=kind,
            is_active=is_active,
        )
        self._by_id[category_id] = category
        return category


@dataclass
class InMemoryTransactionRepository:
    """Implements modules.transactions.domain.repositories.TransactionRepository in memory."""

    _by_id: dict[int, Transaction] = field(default_factory=dict)
    _next_id: int = field(default=1)

    def save(
        self,
        owner_id: int,
        account_id: int,
        category_id: Optional[int],
        kind: str,
        amount: Decimal,
        date: date,
        description: str,
        transfer_group_id: Optional[UUID],
        source: str = "",
        external_reference: str = "",
    ) -> Transaction:
        transaction_id = self._next_id
        self._next_id += 1
        tx = Transaction(
            id=transaction_id,
            owner_id=owner_id,
            account_id=account_id,
            category_id=category_id,
            kind=kind,
            amount=amount.quantize(Decimal("0.01")),
            date=date,
            description=description,
            transfer_group_id=transfer_group_id,
            source=source,
            external_reference=external_reference,
        )
        self._by_id[transaction_id] = tx
        return tx

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
        for tx in self._by_id.values():
            if (
                tx.owner_id == owner_id
                and tx.account_id == account_id
                and tx.source == source
                and tx.external_reference == external_reference
                and tx.date == date
                and tx.amount == amount.quantize(Decimal("0.01"))
                and tx.description == description
            ):
                return tx
        return None

    def find_by_id(self, transaction_id: int) -> Optional[Transaction]:
        return self._by_id.get(transaction_id)

    def list_by_owner(
        self,
        owner_id: int,
        account_id: Optional[int] = None,
        kind: Optional[str] = None,
        category_id: Optional[int] = None,
        category_id_isnull: bool = False,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> list[Transaction]:
        result = list(self._by_id.values())
        result = [t for t in result if t.owner_id == owner_id]
        if account_id is not None:
            result = [t for t in result if t.account_id == account_id]
        if kind is not None:
            result = [t for t in result if t.kind == kind]
        if category_id_isnull:
            result = [t for t in result if t.category_id is None]
        elif category_id is not None:
            result = [t for t in result if t.category_id == category_id]
        if date_from is not None:
            result = [t for t in result if t.date >= date_from]
        if date_to is not None:
            result = [t for t in result if t.date <= date_to]
        result.sort(key=lambda t: (t.date, t.created_at), reverse=True)
        return result

    def update(
        self,
        transaction_id: int,
        amount: Optional[Decimal] = None,
        date: Optional[date] = None,
        description: Optional[str] = None,
        category_id: object = UNSET,
    ) -> Transaction:
        current = self._by_id[transaction_id]
        updated = replace(
            current,
            amount=amount.quantize(Decimal("0.01")) if amount is not None else current.amount,
            date=date if date is not None else current.date,
            description=description if description is not None else current.description,
            category_id=category_id if category_id is not UNSET else current.category_id,
        )
        self._by_id[transaction_id] = updated
        return updated

    def delete(self, transaction_id: int) -> None:
        self._by_id.pop(transaction_id, None)

    def delete_transfer_group(self, transfer_group_id: UUID) -> None:
        to_remove = [
            tid for tid, t in self._by_id.items()
            if t.transfer_group_id == transfer_group_id
        ]
        for tid in to_remove:
            self._by_id.pop(tid, None)

    def create_transfer(
        self,
        owner_id: int,
        source_account_id: int,
        destination_account_id: int,
        amount: Decimal,
        date: date,
        description: str,
        category_id: Optional[int],
    ) -> tuple[Transaction, Transaction]:
        group_id = uuid.uuid4()
        source_tx = self.save(
            owner_id=owner_id,
            account_id=source_account_id,
            category_id=category_id,
            kind="expense",
            amount=amount,
            date=date,
            description=description,
            transfer_group_id=group_id,
        )
        destination_tx = self.save(
            owner_id=owner_id,
            account_id=destination_account_id,
            category_id=category_id,
            kind="income",
            amount=amount,
            date=date,
            description=description,
            transfer_group_id=group_id,
        )
        return source_tx, destination_tx

    def seed(
        self,
        owner_id: int,
        account_id: int,
        kind: str,
        amount: Decimal,
        date: date,
        category_id: Optional[int] = None,
        description: str = "",
        transfer_group_id: Optional[UUID] = None,
        source: str = "",
        external_reference: str = "",
    ) -> Transaction:
        transaction_id = self._next_id
        self._next_id += 1
        tx = Transaction(
            id=transaction_id,
            owner_id=owner_id,
            account_id=account_id,
            category_id=category_id,
            kind=kind,
            amount=amount.quantize(Decimal("0.01")),
            date=date,
            description=description,
            transfer_group_id=transfer_group_id,
            source=source,
            external_reference=external_reference,
        )
        self._by_id[transaction_id] = tx
        return tx


@dataclass
class InMemoryCategorizationRuleRepository:
    """Implements modules.categorization_rules.domain.repositories.CategorizationRuleRepository in memory."""

    _by_id: dict[int, CategorizationRule] = field(default_factory=dict)
    _next_id: int = field(default=1)

    def save(
        self,
        owner_id: int,
        pattern: str,
        match_type: str,
        category_id: int,
        kind: str,
        priority: int,
    ) -> CategorizationRule:
        rule_id = self._next_id
        self._next_id += 1
        rule = CategorizationRule(
            id=rule_id,
            owner_id=owner_id,
            pattern=pattern,
            match_type=match_type,
            category_id=category_id,
            kind=kind,
            priority=priority,
            is_active=True,
        )
        self._by_id[rule_id] = rule
        return rule

    def find_by_id(self, rule_id: int) -> Optional[CategorizationRule]:
        return self._by_id.get(rule_id)

    def list_by_owner(self, owner_id: int) -> list[CategorizationRule]:
        rules = [r for r in self._by_id.values() if r.owner_id == owner_id]
        rules.sort(key=lambda r: (r.priority, r.created_at), reverse=True)
        return rules

    def list_active_by_owner(self, owner_id: int) -> list[CategorizationRule]:
        rules = [
            r for r in self._by_id.values()
            if r.owner_id == owner_id and r.is_active
        ]
        rules.sort(key=lambda r: (r.priority, r.created_at), reverse=True)
        return rules

    def update(
        self,
        rule_id: int,
        pattern: Optional[str] = None,
        match_type: Optional[str] = None,
        category_id: Optional[int] = None,
        kind: Optional[str] = None,
        priority: Optional[int] = None,
    ) -> CategorizationRule:
        current = self._by_id[rule_id]
        updated = replace(
            current,
            pattern=pattern if pattern is not None else current.pattern,
            match_type=match_type if match_type is not None else current.match_type,
            category_id=category_id if category_id is not None else current.category_id,
            kind=kind if kind is not None else current.kind,
            priority=priority if priority is not None else current.priority,
        )
        self._by_id[rule_id] = updated
        return updated

    def deactivate(self, rule_id: int) -> CategorizationRule:
        current = self._by_id[rule_id]
        updated = replace(current, is_active=False)
        self._by_id[rule_id] = updated
        return updated

    def activate(self, rule_id: int) -> CategorizationRule:
        current = self._by_id[rule_id]
        updated = replace(current, is_active=True)
        self._by_id[rule_id] = updated
        return updated

    def delete(self, rule_id: int) -> None:
        self._by_id.pop(rule_id, None)

    def exists_active_duplicate_for_owner(
        self,
        owner_id: int,
        pattern: str,
        match_type: str,
        exclude_id: Optional[int] = None,
    ) -> bool:
        return any(
            r.owner_id == owner_id
            and r.pattern == pattern
            and r.match_type == match_type
            and r.is_active
            and r.id != exclude_id
            for r in self._by_id.values()
        )

    def seed(
        self,
        owner_id: int,
        pattern: str,
        match_type: str,
        category_id: int,
        kind: str = "expense",
        priority: int = 0,
        is_active: bool = True,
    ) -> CategorizationRule:
        rule_id = self._next_id
        self._next_id += 1
        rule = CategorizationRule(
            id=rule_id,
            owner_id=owner_id,
            pattern=pattern,
            match_type=match_type,
            category_id=category_id,
            kind=kind,
            priority=priority,
            is_active=is_active,
        )
        self._by_id[rule_id] = rule
        return rule


@dataclass
class FakeCategoryNameResolver:
    """Implements modules.categorization_rules.application.ports.CategoryNameResolver.

    Backed by an InMemoryCategoryRepository to resolve category names.
    """

    category_repository: InMemoryCategoryRepository

    def find_name_by_id_and_owner(
        self, owner_id: int, category_id: int
    ) -> Optional[str]:
        category = self.category_repository.find_by_id(category_id)
        if category is None or category.owner_id != owner_id:
            return None
        return category.name
