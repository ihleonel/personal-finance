from __future__ import annotations

from rest_framework import serializers

from modules.transactions.models import Transaction


class CreateTransactionSerializer(serializers.Serializer):
    account_id = serializers.IntegerField(
        error_messages={
            "required": "La cuenta es obligatoria.",
            "invalid": "La cuenta no es válida.",
            "null": "La cuenta es obligatoria.",
        },
    )
    kind = serializers.ChoiceField(
        choices=Transaction.Kind.choices,
        error_messages={
            "required": "El tipo de transacción es obligatorio.",
            "invalid_choice": "El tipo de transacción no es válido.",
            "null": "El tipo de transacción es obligatorio.",
        },
    )
    amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        error_messages={
            "required": "El monto es obligatorio.",
            "invalid": "El monto debe ser un número válido.",
            "max_digits": "El monto no puede tener más de 14 dígitos.",
            "max_decimal_places": "El monto no puede tener más de 2 decimales.",
            "max_whole_digits": "El monto no puede tener más de 14 dígitos.",
        },
    )
    date = serializers.DateField(
        error_messages={
            "required": "La fecha es obligatoria.",
            "invalid": "La fecha no es válida.",
            "null": "La fecha es obligatoria.",
        },
    )
    category_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "La categoría no es válida.",
        },
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        error_messages={
            "max_length": "La descripción no puede tener más de 255 caracteres.",
            "null": "La descripción no puede ser nula.",
        },
    )

    def to_dto(self) -> dict:
        data = self.validated_data
        return {
            "account_id": data["account_id"],
            "kind": data["kind"],
            "amount": str(data["amount"]),
            "date": data["date"].isoformat(),
            "category_id": data.get("category_id"),
            "description": data.get("description", ""),
        }


class UpdateTransactionSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "El monto debe ser un número válido.",
            "max_digits": "El monto no puede tener más de 14 dígitos.",
            "max_decimal_places": "El monto no puede tener más de 2 decimales.",
            "max_whole_digits": "El monto no puede tener más de 14 dígitos.",
        },
    )
    date = serializers.DateField(
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "La fecha no es válida.",
            "null": "La fecha no puede ser nula.",
        },
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        error_messages={
            "max_length": "La descripción no puede tener más de 255 caracteres.",
            "null": "La descripción no puede ser nula.",
        },
    )
    category_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "La categoría no es válida.",
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
        if "amount" in data:
            amount = data["amount"]
            out["amount"] = "" if amount is None else str(amount)
        if "date" in data:
            d = data["date"]
            out["date"] = "" if d is None else d.isoformat()
        if "description" in data:
            out["description"] = data["description"]
        if "category_id" in data:
            out["category_id"] = data["category_id"]
        return out


class ListTransactionsQuerySerializer(serializers.Serializer):
    account_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        error_messages={"invalid": "La cuenta no es válida."},
    )
    kind = serializers.ChoiceField(
        choices=Transaction.Kind.choices,
        required=False,
        allow_null=True,
        error_messages={"invalid_choice": "El tipo de transacción no es válido."},
    )
    category_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        error_messages={"invalid": "La categoría no es válida."},
    )
    category_id_isnull = serializers.BooleanField(
        required=False,
        default=False,
    )
    date_from = serializers.DateField(
        required=False,
        allow_null=True,
        error_messages={"invalid": "La fecha de inicio no es válida."},
    )
    date_to = serializers.DateField(
        required=False,
        allow_null=True,
        error_messages={"invalid": "La fecha de fin no es válida."},
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        error_messages={"invalid": "La descripción no es válida."},
    )

    def to_filters(self) -> dict:
        data = self.validated_data
        out: dict = {}
        for key in ("account_id", "kind", "category_id", "date_from", "date_to"):
            value = data.get(key)
            if value is not None:
                if key in ("date_from", "date_to") and hasattr(value, "isoformat"):
                    out[key] = value.isoformat()
                else:
                    out[key] = value
        if data.get("category_id_isnull"):
            out["category_id_isnull"] = True
        description = data.get("description")
        if description:
            out["description"] = description
        return out


class BulkAssignCategorySerializer(serializers.Serializer):
    transaction_ids = serializers.ListField(
        child=serializers.IntegerField(
            error_messages={
                "invalid": "La transacción no es válida.",
            },
        ),
        min_length=1,
        error_messages={
            "required": "Seleccioná al menos una transacción.",
            "empty": "Seleccioná al menos una transacción.",
            "not_a_list": "La lista de transacciones no es válida.",
        },
    )
    category_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "La categoría no es válida.",
        },
    )
