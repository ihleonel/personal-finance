from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from django.contrib.auth.hashers import check_password, make_password
from django.utils.translation import gettext_lazy as _

from modules.auths.application.dtos import ChangePasswordInput
from modules.auths.application.result import Result
from modules.auths.domain.repositories import UserRepository


_MIN_PASSWORD_LENGTH = 8


@dataclass
class ChangePasswordUseCase:
    repository: UserRepository

    def execute(self, user_id: int, data: ChangePasswordInput) -> Result[None]:
        result = Result[None]()

        user = self.repository.find_by_id(user_id)
        if user is None:
            result.add_error(
                "non_field_errors",
                "auth.user.not_found",
                str(_("Usuario no encontrado.")),
            )
            return result

        if not data.current_password or not isinstance(data.current_password, str):
            result.add_error(
                "current_password",
                "auth.password.required",
                str(_("La contraseña actual es obligatoria.")),
            )

        if not data.new_password or not isinstance(data.new_password, str):
            result.add_error(
                "new_password",
                "auth.password.required",
                str(_("La nueva contraseña es obligatoria.")),
            )
        elif len(data.new_password) < _MIN_PASSWORD_LENGTH:
            result.add_error(
                "new_password",
                "auth.password.too_short",
                str(_("La contraseña debe tener al menos 8 caracteres.")),
            )

        if result.has_errors:
            return result

        password_hash = self.repository.get_password_hash(user.email)
        if not password_hash or not check_password(data.current_password, password_hash):
            result.add_error(
                "current_password",
                "auth.password.invalid_credentials",
                str(_("La contraseña actual es incorrecta.")),
            )
            return result

        if data.current_password == data.new_password:
            result.add_error(
                "new_password",
                "auth.password.same_password",
                str(_("La nueva contraseña no puede ser igual a la contraseña actual.")),
            )
            return result

        new_hash = make_password(data.new_password)
        self.repository.update_password(user_id, new_hash)

        return Result.ok(str(_("Contraseña actualizada.")))