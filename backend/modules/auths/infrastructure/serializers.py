from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(
        error_messages={
            "required": "El correo electrónico es obligatorio.",
            "invalid": "Ingresa un correo electrónico válido.",
            "blank": "El correo electrónico no puede estar vacío.",
            "null": "El correo electrónico es obligatorio.",
        }
    )
    password = serializers.CharField(
        min_length=8,
        write_only=True,
        error_messages={
            "required": "La contraseña es obligatoria.",
            "blank": "La contraseña no puede estar vacía.",
            "min_length": "La contraseña debe tener al menos 8 caracteres.",
            "null": "La contraseña es obligatoria.",
        },
    )
    first_name = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        error_messages={
            "max_length": "El nombre no puede tener más de 150 caracteres.",
            "null": "El nombre no puede ser nulo.",
        },
    )
    last_name = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        error_messages={
            "max_length": "El apellido no puede tener más de 150 caracteres.",
            "null": "El apellido no puede ser nulo.",
        },
    )

    def to_dto(self) -> dict:
        data = self.validated_data
        return {
            "email": data["email"],
            "password": data["password"],
            "first_name": data.get("first_name", ""),
            "last_name": data.get("last_name", ""),
        }


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        error_messages={
            "required": "El correo electrónico es obligatorio.",
            "invalid": "Ingresa un correo electrónico válido.",
            "blank": "El correo electrónico no puede estar vacío.",
            "null": "El correo electrónico es obligatorio.",
        }
    )
    password = serializers.CharField(
        write_only=True,
        error_messages={
            "required": "La contraseña es obligatoria.",
            "blank": "La contraseña no puede estar vacía.",
            "null": "La contraseña es obligatoria.",
        },
    )

    def to_dto(self) -> dict:
        return {
            "email": self.validated_data["email"],
            "password": self.validated_data["password"],
        }


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        error_messages={
            "required": "El token de actualización es obligatorio.",
            "blank": "El token de actualización no puede estar vacío.",
            "null": "El token de actualización es obligatorio.",
        }
    )


class ProfileSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)


class UpdateProfileSerializer(serializers.Serializer):
    first_name = serializers.CharField(
        required=False,
        allow_blank=False,
        max_length=150,
        error_messages={
            "required": "El nombre es obligatorio.",
            "blank": "El nombre no puede estar vacío.",
            "max_length": "El nombre no puede tener más de 150 caracteres.",
            "null": "El nombre no puede ser nulo.",
        },
    )
    last_name = serializers.CharField(
        required=False,
        allow_blank=False,
        max_length=150,
        error_messages={
            "required": "El apellido es obligatorio.",
            "blank": "El apellido no puede estar vacío.",
            "max_length": "El apellido no puede tener más de 150 caracteres.",
            "null": "El apellido no puede ser nulo.",
        },
    )

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                "Proporciona al menos uno de los campos: nombre o apellido."
            )
        return attrs

    def to_dto(self) -> dict:
        return {
            "first_name": self.validated_data.get("first_name", ""),
            "last_name": self.validated_data.get("last_name", ""),
        }


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        write_only=True,
        error_messages={
            "required": "La contraseña actual es obligatoria.",
            "blank": "La contraseña actual no puede estar vacía.",
            "null": "La contraseña actual es obligatoria.",
        },
    )
    new_password = serializers.CharField(
        min_length=8,
        write_only=True,
        error_messages={
            "required": "La nueva contraseña es obligatoria.",
            "blank": "La nueva contraseña no puede estar vacía.",
            "min_length": "La contraseña debe tener al menos 8 caracteres.",
            "null": "La nueva contraseña es obligatoria.",
        },
    )

    def to_dto(self) -> dict:
        return {
            "current_password": self.validated_data["current_password"],
            "new_password": self.validated_data["new_password"],
        }