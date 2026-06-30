from __future__ import annotations

from dataclasses import dataclass


_ALLOWED_CURRENCIES = frozenset({"ARS", "USD", "EUR"})
_ALLOWED_ACCOUNT_TYPES = frozenset(
    {"cash", "bank", "credit_card", "savings", "investment", "other"}
)


class InvalidCurrencyError(ValueError):
    pass


class InvalidAccountTypeError(ValueError):
    pass


@dataclass(frozen=True)
class Currency:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or self.value not in _ALLOWED_CURRENCIES:
            raise InvalidCurrencyError(f"Invalid currency: {self.value!r}")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def try_parse(cls, raw: object) -> "Currency | None":
        if not isinstance(raw, str):
            return None
        try:
            return cls(raw)
        except InvalidCurrencyError:
            return None


@dataclass(frozen=True)
class AccountType:
    value: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.value, str)
            or self.value not in _ALLOWED_ACCOUNT_TYPES
        ):
            raise InvalidAccountTypeError(f"Invalid account type: {self.value!r}")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def try_parse(cls, raw: object) -> "AccountType | None":
        if not isinstance(raw, str):
            return None
        try:
            return cls(raw)
        except InvalidAccountTypeError:
            return None


allowed_currencies = _ALLOWED_CURRENCIES
allowed_account_types = _ALLOWED_ACCOUNT_TYPES