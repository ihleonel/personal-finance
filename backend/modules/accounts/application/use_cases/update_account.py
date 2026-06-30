from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional

from django.utils.translation import gettext_lazy as _

from modules.accounts.application.dtos import UpdateAccountInput, AccountOutput
from modules.accounts.domain.repositories import AccountRepository
from modules.accounts.domain.value_objects import AccountType, Currency
from modules.shared.application.result import Result


_MAX_NAME_LENGTH = 100
_MAX_BALANCE_DIGITS = 14


@dataclass
class UpdateAccountUseCase:
    repository: AccountRepository

    def execute(
        self, owner_id: int, account_id: int, data: UpdateAccountInput
    ) -> Result[AccountOutput]:
        result = Result[AccountOutput]()

        account = self.repository.find_by_id(account_id)
        if account is None or account.owner_id != owner_id:
            result.add_error(
                "non_field_errors",
                "accounts.account.not_found",
                str(_("Cuenta no encontrada.")),
            )
            return result

        if not account.is_active:
            result.add_error(
                "non_field_errors",
                "accounts.account.inactive",
                str(_("La cuenta está inactiva y no se puede editar.")),
            )
            return result

        has_any_field = any(
            getattr(data, f) is not None for f in ("name", "account_type", "currency", "initial_balance")
        )
        if not has_any_field:
            result.add_error(
                "non_field_errors",
                "accounts.account.empty_payload",
                str(_("Proporciona al menos un campo para actualizar.")),
            )
            return result

        new_name: Optional[str] = None
        new_type: Optional[str] = None
        new_currency: Optional[str] = None
        new_balance: Optional[Decimal] = None

        if data.name is not None:
            if not data.name.strip():
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
            new_name = data.name

        if data.account_type is not None:
            parsed_type = AccountType.try_parse(data.account_type)
            if parsed_type is None:
                result.add_error(
                    "account_type",
                    "accounts.account_type.invalid",
                    str(_("El tipo de cuenta no es válido.")),
                )
            new_type = parsed_type.value if parsed_type is not None else None

        if data.currency is not None:
            parsed_currency = Currency.try_parse(data.currency)
            if parsed_currency is None:
                result.add_error(
                    "currency",
                    "accounts.currency.invalid",
                    str(_("La moneda no es válida. Valores admitidos: ARS, USD, EUR.")),
                )
            new_currency = parsed_currency.value if parsed_currency is not None else None

        if data.initial_balance is not None:
            parsed_balance = self._parse_balance(data.initial_balance)
            if parsed_balance is None:
                result.add_error(
                    "initial_balance",
                    "accounts.initial_balance.invalid",
                    str(_("El saldo inicial debe ser un número válido.")),
                )
            elif len(parsed_balance.as_tuple().digits) > _MAX_BALANCE_DIGITS:
                result.add_error(
                    "initial_balance",
                    "accounts.initial_balance.max_digits",
                    str(_("El saldo inicial no puede tener más de 14 dígitos.")),
                )
            new_balance = parsed_balance

        if (
            new_name is not None
            and new_name != account.name
            and self.repository.exists_active_name_for_owner(owner_id, new_name)
        ):
            result.add_error(
                "name",
                "accounts.name.already_exists",
                str(_("Ya tenés una cuenta activa con ese nombre.")),
            )

        if result.has_errors:
            return result

        updated = self.repository.update(
            account_id=account_id,
            name=new_name,
            account_type=new_type,
            currency=new_currency,
            initial_balance=new_balance,
        )

        return Result.ok(
            AccountOutput(
                id=updated.id or 0,
                owner_id=updated.owner_id,
                name=updated.name,
                account_type=updated.account_type,
                currency=updated.currency,
                initial_balance=str(updated.initial_balance),
                is_active=updated.is_active,
            )
        )

    @staticmethod
    def _parse_balance(raw: object) -> Decimal | None:
        try:
            return Decimal(str(raw)).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError):
            return None