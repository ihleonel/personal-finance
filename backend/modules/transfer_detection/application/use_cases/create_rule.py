from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from modules.shared.application.result import Result
from modules.transfer_detection.application.dtos import (
    CreateTransferDetectionRuleInput,
    TransferDetectionRuleOutput,
)
from modules.transfer_detection.domain.repositories import (
    TransferDetectionRuleRepository,
)
from modules.transfer_detection.domain.value_objects import (
    RuleMatchType,
    RulePattern,
    max_pattern_length,
)


@dataclass
class CreateTransferDetectionRuleUseCase:
    repository: TransferDetectionRuleRepository

    def execute(
        self, data: CreateTransferDetectionRuleInput
    ) -> Result[TransferDetectionRuleOutput]:
        result = Result[TransferDetectionRuleOutput]()

        if not data.pattern or not data.pattern.strip():
            result.add_error(
                "pattern",
                "transfer_detection.pattern.required",
                str(_("El patrón es obligatorio.")),
            )
        elif len(data.pattern) > max_pattern_length:
            result.add_error(
                "pattern",
                "transfer_detection.pattern.max_length",
                str(_(f"El patrón no puede tener más de {max_pattern_length} caracteres.")),
            )

        match_type_vo = RuleMatchType.try_parse(data.match_type)
        if match_type_vo is None:
            result.add_error(
                "match_type",
                "transfer_detection.match_type.invalid",
                str(_("El tipo de coincidencia no es válido. Valores admitidos: contains, equals.")),
            )

        if data.priority is None or data.priority < 0:
            result.add_error(
                "priority",
                "transfer_detection.priority.invalid",
                str(_("La prioridad debe ser un número entero no negativo.")),
            )

        if (
            data.pattern
            and data.pattern.strip()
            and match_type_vo is not None
            and self.repository.exists_active_duplicate_for_owner(
                owner_id=data.owner_id,
                pattern=data.pattern,
                match_type=match_type_vo.value,
            )
        ):
            result.add_error(
                "pattern",
                "transfer_detection.pattern.already_exists",
                str(_("Ya tenés una regla activa con ese patrón y tipo de coincidencia.")),
            )

        if result.has_errors:
            return result

        try:
            RulePattern(data.pattern)
        except ValueError:
            result.add_error(
                "pattern",
                "transfer_detection.pattern.invalid",
                str(_("El patrón no es válido.")),
            )
            return result

        saved = self.repository.save(
            owner_id=data.owner_id,
            pattern=data.pattern,
            match_type=match_type_vo.value,  # type: ignore[union-attr]
            priority=data.priority,
        )

        return Result.ok(self._to_output(saved))

    @staticmethod
    def _to_output(rule) -> TransferDetectionRuleOutput:
        return TransferDetectionRuleOutput(
            id=rule.id or 0,
            owner_id=rule.owner_id,
            pattern=rule.pattern,
            match_type=rule.match_type,
            priority=rule.priority,
            is_active=rule.is_active,
        )