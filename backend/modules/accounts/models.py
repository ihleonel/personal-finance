from __future__ import annotations

from django.conf import settings
from django.db import models


class Account(models.Model):
    class AccountType(models.TextChoices):
        CASH = "cash", "Efectivo"
        BANK = "bank", "Banco"
        CREDIT_CARD = "credit_card", "Tarjeta de crédito"
        SAVINGS = "savings", "Ahorro"
        INVESTMENT = "investment", "Inversión"
        OTHER = "other", "Otra"

    class Currency(models.TextChoices):
        ARS = "ARS", "Peso argentino"
        USD = "USD", "Dólar estadounidense"
        EUR = "EUR", "Euro"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="accounts",
    )
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=AccountType.choices)
    currency = models.CharField(max_length=3, choices=Currency.choices)
    initial_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_account"
        verbose_name = "account"
        verbose_name_plural = "accounts"
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name"],
                condition=models.Q(is_active=True),
                name="unique_active_name_per_owner",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.currency})"