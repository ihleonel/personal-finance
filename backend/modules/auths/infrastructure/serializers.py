from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(required=False, allow_blank=True, default="")
    last_name = serializers.CharField(required=False, allow_blank=True, default="")

    def to_dto(self) -> dict:
        data = self.validated_data
        return {
            "email": data["email"],
            "password": data["password"],
            "first_name": data.get("first_name", ""),
            "last_name": data.get("last_name", ""),
        }


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def to_dto(self) -> dict:
        return {"email": self.validated_data["email"], "password": self.validated_data["password"]}


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
