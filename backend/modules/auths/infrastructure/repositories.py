from __future__ import annotations

from typing import Optional

from modules.auths.domain.entities import User
from modules.auths.domain.repositories import UserRepository

from modules.auths.models import User as UserORM


class DjangoUserRepository(UserRepository):
    def exists_by_email(self, email: str) -> bool:
        return UserORM.objects.filter(email__iexact=email).exists()

    def find_by_email(self, email: str) -> Optional[User]:
        try:
            u = UserORM.objects.get(email__iexact=email)
        except UserORM.DoesNotExist:
            return None
        return self._to_entity(u)

    def find_by_id(self, user_id: int) -> Optional[User]:
        try:
            u = UserORM.objects.get(pk=user_id)
        except UserORM.DoesNotExist:
            return None
        return self._to_entity(u)

    def save(
        self,
        email: str,
        password_hash: str,
        first_name: str = "",
        last_name: str = "",
        is_active: bool = True,
    ) -> User:
        u = UserORM(
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
        )
        u.password = password_hash
        u.save()
        return self._to_entity(u)

    def get_password_hash(self, email: str) -> Optional[str]:
        try:
            u = UserORM.objects.only("password").get(email__iexact=email)
        except UserORM.DoesNotExist:
            return None
        return u.password

    def update_password(self, user_id: int, password_hash: str) -> None:
        UserORM.objects.filter(pk=user_id).update(password=password_hash)

    def update(
        self,
        user_id: int,
        first_name: str = "",
        last_name: str = "",
    ) -> User:
        fields: dict[str, str] = {}
        if first_name:
            fields["first_name"] = first_name
        if last_name:
            fields["last_name"] = last_name

        if fields:
            UserORM.objects.filter(pk=user_id).update(**fields)

        return self.find_by_id(user_id)  # type: ignore[return-value]

    @staticmethod
    def _to_entity(u: UserORM) -> User:
        return User(
            id=u.id,
            email=u.email,
            first_name=u.first_name,
            last_name=u.last_name,
            is_active=u.is_active,
            created_at=u.date_joined,
        )
