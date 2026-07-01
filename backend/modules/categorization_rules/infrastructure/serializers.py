from rest_framework import serializers

from modules.categorization_rules.infrastructure.models import (
    CategorizationRule,
)


class CreateCategorizationRuleSerializer(serializers.Serializer):
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
        choices=CategorizationRule.MatchType.choices,
        error_messages={
            "required": "El tipo de coincidencia es obligatorio.",
            "invalid_choice": "El tipo de coincidencia no es válido.",
            "null": "El tipo de coincidencia es obligatorio.",
        },
    )
    category_id = serializers.IntegerField(
        min_value=1,
        error_messages={
            "required": "La categoría es obligatoria.",
            "invalid": "La categoría no es válida.",
            "null": "La categoría es obligatoria.",
        },
    )
    kind = serializers.ChoiceField(
        choices=CategorizationRule.Kind.choices,
        error_messages={
            "required": "El tipo de categoría es obligatorio.",
            "invalid_choice": "El tipo de categoría no es válido.",
            "null": "El tipo de categoría es obligatorio.",
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
            "category_id": data["category_id"],
            "kind": data["kind"],
            "priority": data.get("priority", 0),
        }


class UpdateCategorizationRuleSerializer(serializers.Serializer):
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
        choices=CategorizationRule.MatchType.choices,
        required=False,
        error_messages={
            "invalid_choice": "El tipo de coincidencia no es válido.",
            "null": "El tipo de coincidencia no puede ser nulo.",
        },
    )
    category_id = serializers.IntegerField(
        required=False,
        min_value=1,
        error_messages={
            "invalid": "La categoría no es válida.",
            "min_value": "La categoría es obligatoria.",
        },
    )
    kind = serializers.ChoiceField(
        choices=CategorizationRule.Kind.choices,
        required=False,
        error_messages={
            "invalid_choice": "El tipo de categoría no es válido.",
            "null": "El tipo de categoría no puede ser nulo.",
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
        if "category_id" in data:
            out["category_id"] = data["category_id"]
        if "kind" in data:
            out["kind"] = data["kind"]
        if "priority" in data:
            out["priority"] = data["priority"]
        return out


class SuggestCategorySerializer(serializers.Serializer):
    description = serializers.CharField(
        required=True,
        allow_blank=True,
        error_messages={
            "required": "La descripción es obligatoria.",
        },
    )

    def to_dto(self) -> dict:
        return {"description": self.validated_data["description"]}