from __future__ import annotations

from rest_framework import serializers


class IncomeExpenseSummaryQuerySerializer(serializers.Serializer):
    period = serializers.ChoiceField(
        choices=[("week", "week"), ("month", "month"), ("year", "year")],
        error_messages={
            "required": "El periodo es obligatorio.",
            "invalid_choice": "El periodo debe ser 'week', 'month' o 'year'.",
            "null": "El periodo es obligatorio.",
        },
    )
    periods_count = serializers.IntegerField(
        min_value=1,
        max_value=12,
        error_messages={
            "required": "La cantidad de periodos es obligatoria.",
            "invalid": "La cantidad de periodos no es válida.",
            "null": "La cantidad de periodos es obligatoria.",
            "min_value": "La cantidad de periodos debe ser un entero entre 1 y 12.",
            "max_value": "La cantidad de periodos debe ser un entero entre 1 y 12.",
        },
    )
    account_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        error_messages={"invalid": "La cuenta no es válida."},
    )

    def to_dto(self) -> dict:
        data = self.validated_data
        return {
            "period": data["period"],
            "periods_count": data["periods_count"],
            "account_id": data.get("account_id"),
        }


class CategorySummaryQuerySerializer(serializers.Serializer):
    period = serializers.ChoiceField(
        choices=[("week", "week"), ("month", "month"), ("year", "year")],
        error_messages={
            "required": "El periodo es obligatorio.",
            "invalid_choice": "El periodo debe ser 'week', 'month' o 'year'.",
            "null": "El periodo es obligatorio.",
        },
    )
    periods_count = serializers.IntegerField(
        min_value=1,
        max_value=12,
        error_messages={
            "required": "La cantidad de periodos es obligatoria.",
            "invalid": "La cantidad de periodos no es válida.",
            "null": "La cantidad de periodos es obligatoria.",
            "min_value": "La cantidad de periodos debe ser un entero entre 1 y 12.",
            "max_value": "La cantidad de periodos debe ser un entero entre 1 y 12.",
        },
    )
    account_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        error_messages={"invalid": "La cuenta no es válida."},
    )

    def to_dto(self) -> dict:
        data = self.validated_data
        return {
            "period": data["period"],
            "periods_count": data["periods_count"],
            "account_id": data.get("account_id"),
        }