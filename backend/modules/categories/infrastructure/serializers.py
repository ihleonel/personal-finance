from rest_framework import serializers

from modules.categories.models import Category


class CreateCategorySerializer(serializers.Serializer):
    name = serializers.CharField(
        max_length=100,
        error_messages={
            "required": "El nombre de la categoría es obligatorio.",
            "blank": "El nombre de la categoría es obligatorio.",
            "max_length": "Asegúrate de que el nombre no tenga más de 100 caracteres.",
            "null": "El nombre de la categoría es obligatorio.",
        },
    )
    kind = serializers.ChoiceField(
        choices=Category.Kind.choices,
        error_messages={
            "required": "El tipo de categoría es obligatorio.",
            "invalid_choice": "El tipo de categoría no es válido.",
            "null": "El tipo de categoría es obligatorio.",
        },
    )
    include_in_summaries = serializers.BooleanField(
        required=False,
        default=True,
    )

    def to_dto(self) -> dict:
        data = self.validated_data
        return {
            "name": data["name"],
            "kind": data["kind"],
            "include_in_summaries": data.get("include_in_summaries", True),
        }


class UpdateCategorySerializer(serializers.Serializer):
    name = serializers.CharField(
        required=False,
        allow_blank=False,
        max_length=100,
        error_messages={
            "blank": "El nombre de la categoría es obligatorio.",
            "max_length": "Asegúrate de que el nombre no tenga más de 100 caracteres.",
            "null": "El nombre no puede ser nulo.",
        },
    )
    kind = serializers.ChoiceField(
        choices=Category.Kind.choices,
        required=False,
        error_messages={
            "invalid_choice": "El tipo de categoría no es válido.",
            "null": "El tipo de categoría no puede ser nulo.",
        },
    )
    include_in_summaries = serializers.BooleanField(
        required=False,
        allow_null=True,
        default=None,
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
        if "name" in data:
            out["name"] = data["name"]
        if "kind" in data:
            out["kind"] = data["kind"]
        if "include_in_summaries" in data and data["include_in_summaries"] is not None:
            out["include_in_summaries"] = data["include_in_summaries"]
        return out