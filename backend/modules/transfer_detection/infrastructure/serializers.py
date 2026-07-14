from rest_framework import serializers

from modules.transfer_detection.infrastructure.models import (
    TransferDetectionRule,
)


class CreateTransferDetectionRuleSerializer(serializers.Serializer):
    pattern = serializers.CharField(
        max_length=120,
        error_messages={
            "required": "El patrón es obligatorio.",
            "blank": "El patrón es obligatorio.",
            "max_length": "El patrón no puede tener más de 120 caracteres.",
            "null": "El patrón es obligatorio.",
        },
    )
    match_type = serializers.ChoiceField(
        choices=TransferDetectionRule.MatchType.choices,
        error_messages={
            "required": "El tipo de coincidencia es obligatorio.",
            "invalid_choice": "El tipo de coincidencia no es válido.",
            "null": "El tipo de coincidencia es obligatorio.",
        },
    )
    priority = serializers.IntegerField(
        min_value=0,
        default=0,
        error_messages={
            "invalid": "La prioridad debe ser un número entero no negativo.",
        },
    )

    def to_dto(self) -> dict:
        data = self.validated_data
        return {
            "pattern": data["pattern"],
            "match_type": data["match_type"],
            "priority": data.get("priority", 0),
        }


class UpdateTransferDetectionRuleSerializer(serializers.Serializer):
    pattern = serializers.CharField(
        required=False,
        allow_blank=False,
        max_length=120,
        error_messages={
            "blank": "El patrón es obligatorio.",
            "max_length": "El patrón no puede tener más de 120 caracteres.",
            "null": "El patrón no puede ser nulo.",
        },
    )
    match_type = serializers.ChoiceField(
        choices=TransferDetectionRule.MatchType.choices,
        required=False,
        error_messages={
            "invalid_choice": "El tipo de coincidencia no es válido.",
            "null": "El tipo de coincidencia no puede ser nulo.",
        },
    )
    priority = serializers.IntegerField(
        required=False,
        min_value=0,
        error_messages={
            "invalid": "La prioridad debe ser un número entero no negativo.",
        },
    )

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                "Proporciona al menos un campo para actualizar."
            )
        return attrs

    def to_dto(self) -> dict:
        data = self.validated_data
        out: dict = {}
        if "pattern" in data:
            out["pattern"] = data["pattern"]
        if "match_type" in data:
            out["match_type"] = data["match_type"]
        if "priority" in data:
            out["priority"] = data["priority"]
        return out


class SuggestTransferSerializer(serializers.Serializer):
    description = serializers.CharField(
        required=True,
        allow_blank=True,
        error_messages={
            "required": "La descripción es obligatoria.",
        },
    )

    def to_dto(self) -> dict:
        return {"description": self.validated_data["description"]}


class DetectTransfersSerializer(serializers.Serializer):
    account_id = serializers.IntegerField(
        required=False,
        min_value=1,
        allow_null=True,
        error_messages={
            "invalid": "La cuenta no es válida.",
        },
    )
    date_from = serializers.DateField(
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "La fecha desde no es válida.",
        },
    )
    date_to = serializers.DateField(
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "La fecha hasta no es válida.",
        },
    )
    window_days = serializers.IntegerField(
        required=False,
        min_value=0,
        max_value=30,
        default=3,
        error_messages={
            "invalid": "La ventana de días debe ser un entero entre 0 y 30.",
        },
    )
    amount_tolerance = serializers.CharField(
        required=False,
        default="0.00",
        error_messages={
            "invalid": "La tolerancia de monto no es válida.",
        },
    )

    def to_dto(self) -> dict:
        data = self.validated_data
        return {
            "account_id": data.get("account_id"),
            "date_from": data.get("date_from"),
            "date_to": data.get("date_to"),
            "window_days": data.get("window_days", 3),
            "amount_tolerance": data.get("amount_tolerance", "0.00"),
        }