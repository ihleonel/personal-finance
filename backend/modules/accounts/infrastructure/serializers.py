from rest_framework import serializers

from modules.accounts.models import Account


class CreateAccountSerializer(serializers.Serializer):
    name = serializers.CharField(
        max_length=100,
        error_messages={
            "required": "El nombre de la cuenta es obligatorio.",
            "blank": "El nombre de la cuenta es obligatorio.",
            "max_length": "Asegúrate de que el nombre no tenga más de 100 caracteres.",
            "null": "El nombre de la cuenta es obligatorio.",
        },
    )
    account_type = serializers.ChoiceField(
        choices=Account.AccountType.choices,
        error_messages={
            "required": "El tipo de cuenta es obligatorio.",
            "invalid_choice": "El tipo de cuenta no es válido.",
            "null": "El tipo de cuenta es obligatorio.",
        },
    )
    currency = serializers.ChoiceField(
        choices=Account.Currency.choices,
        error_messages={
            "required": "La moneda es obligatoria.",
            "invalid_choice": "La moneda no es válida.",
            "null": "La moneda es obligatoria.",
        },
    )
    initial_balance = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "El saldo inicial debe ser un número válido.",
            "max_digits": "El saldo inicial no puede tener más de 14 dígitos.",
            "max_decimal_places": "El saldo inicial no puede tener más de 2 decimales.",
        },
    )

    def to_dto(self) -> dict:
        data = self.validated_data
        balance = data.get("initial_balance")
        return {
            "name": data["name"],
            "account_type": data["account_type"],
            "currency": data["currency"],
            "initial_balance": "" if balance is None else str(balance),
        }


class UpdateAccountSerializer(serializers.Serializer):
    name = serializers.CharField(
        required=False,
        allow_blank=False,
        max_length=100,
        error_messages={
            "blank": "El nombre de la cuenta es obligatorio.",
            "max_length": "Asegúrate de que el nombre no tenga más de 100 caracteres.",
            "null": "El nombre no puede ser nulo.",
        },
    )
    account_type = serializers.ChoiceField(
        choices=Account.AccountType.choices,
        required=False,
        error_messages={
            "invalid_choice": "El tipo de cuenta no es válido.",
            "null": "El tipo de cuenta no puede ser nulo.",
        },
    )
    currency = serializers.ChoiceField(
        choices=Account.Currency.choices,
        required=False,
        error_messages={
            "invalid_choice": "La moneda no es válida.",
            "null": "La moneda no puede ser nula.",
        },
    )
    initial_balance = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        required=False,
        allow_null=True,
        error_messages={
            "invalid": "El saldo inicial debe ser un número válido.",
            "max_digits": "El saldo inicial no puede tener más de 14 dígitos.",
            "max_decimal_places": "El saldo inicial no puede tener más de 2 decimales.",
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
        if "name" in data:
            out["name"] = data["name"]
        if "account_type" in data:
            out["account_type"] = data["account_type"]
        if "currency" in data:
            out["currency"] = data["currency"]
        if "initial_balance" in data:
            balance = data["initial_balance"]
            out["initial_balance"] = "" if balance is None else str(balance)
        return out