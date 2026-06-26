from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from modules.auths.application.dtos import UpdateProfileInput, UserOutput
from modules.auths.application.result import Result
from modules.auths.domain.repositories import UserRepository


_MAX_FIELD_LENGTH = 150


@dataclass
class UpdateUserProfileUseCase:
    repository: UserRepository

    def execute(self, user_id: int, data: UpdateProfileInput) -> Result[UserOutput]:
        result = Result[UserOutput]()

        if self.repository.find_by_id(user_id) is None:
            result.add_error(
                "non_field_errors",
                "auth.user.not_found",
                str(_("Usuario no encontrado.")),
            )
            return result

        if not data.first_name and not data.last_name:
            result.add_error(
                "non_field_errors",
                "auth.profile.empty_payload",
                str(_("Proporciona al menos uno de los campos: nombre o apellido.")),
            )
            return result

        for field_name, value in (
            ("first_name", data.first_name),
            ("last_name", data.last_name),
        ):
            if value and len(value) > _MAX_FIELD_LENGTH:
                result.add_error(
                    field_name,
                    "auth.field.max_length",
                    str(_("Asegúrate de que este campo no tenga más de 150 caracteres.")),
                )

        if result.has_errors:
            return result

        updated = self.repository.update(
            user_id=user_id,
            first_name=data.first_name,
            last_name=data.last_name,
        )

        return Result.ok(
            UserOutput(
                id=updated.id or 0,
                email=updated.email,
                first_name=updated.first_name,
                last_name=updated.last_name,
                is_active=updated.is_active,
            )
        )