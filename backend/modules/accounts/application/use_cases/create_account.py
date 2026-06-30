from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.utils.translation import gettext_lazy as _

from modules.accounts.application.dtos import CreateAccountInput, AccountOutput
from modules.accounts.domain.repositories import AccountRepository
from modules.accounts.domain.value_objects import AccountType, Currency
from modules.shared.application.result import Result


_MAX_NAME_LENGTH = 100
_MAX_BALANCE_DIGITS = 14
_BALANCE_PLACES = 2


@dataclass
class CreateAccountUseCase:
    repository: AccountRepository

    def execute(self, data: CreateAccountInput) -> Result[AccountOutput]:
        result = Result[AccountOutput]()

        if not data.name or not data.name.strip():
            result.add_error(
                "name",
                "accounts.name.required",
                str(_("El nombre de la cuenta es obligatorio.")),
            )
        elif len(data.name) > _MAX_NAME_LENGTH:
            result.add_error(
                "name",
                "accounts.name.max_length",
                str(_("Asegúrate de que el nombre no tenga más de 100 caracteres.")),
            )

        currency = Currency.try_parse(data.currency)
        if currency is None:
            result.add_error(
                "currency",
                "accounts.currency.invalid",
                str(_("La moneda no es válida. Valores admitidos: ARS, USD, EUR.")),
            )

        account_type = AccountType.try_parse(data.account_type)
        if account_type is None:
            result.add_error(
                "account_type",
                "accounts.account_type.invalid",
                str(_("El tipo de cuenta no es válido.")),
            )

        initial_balance = self._parse_balance(data.initial_balance, result)
        if initial_balance is not None and len(initial_balance.as_tuple().digits) > _MAX_BALANCE_DIGITS:
            result.add_error(
                "initial_balance",
                "accounts.initial_balance.max_digits",
                str(_("El saldo inicial no puede tener más de 14 dígitos.")),
            )

        if (
            data.name
            and data.name.strip()
            and self.repository.exists_active_name_for_owner(data.owner_id, data.name)
        ):
            result.add_error(
                "name",
                "accounts.name.already_exists",
                str(_("Ya tenés una cuenta activa con ese nombre.")),
            )

        if result.has_errors:
            return result

        saved = self.repository.save(
            owner_id=data.owner_id,
            name=data.name,
            account_type=account_type.value,  # type: ignore[union-attr]
            currency=currency.value,  # type: ignore[union-attr]
            initial_balance=initial_balance,  # type: ignore[arg-type]
        )

        return Result.ok(self._to_output(saved))

    @staticmethod
    def _parse_balance(raw: object, result: Result) -> Decimal | None:
        if raw is None:
            return Decimal("0")
        try:
            value = Decimal(str(raw))
        except (InvalidOperation, ValueError):
            result.add_error(
                "initial_balance",
                "accounts.initial_balance.invalid",
                str(_("El saldo inicial debe ser un número válido.")),
            )
            return None
        return value.quantize(Decimal("0.01"))

    @staticmethod
    def _to_output(account) -> AccountOutput:
        return AccountOutput(
            id=account.id,
            owner_id=account.owner_id,
            name=account.name,
            account_type=account.account_type,
            currency=account.currency,
            initial_balance=str(account.initial_balance),
            is_active=account.is_active,
        )