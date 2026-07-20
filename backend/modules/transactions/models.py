from __future__ import annotations

from django.conf import settings
from django.db import models


class Transaction(models.Model):
    class Kind(models.TextChoices):
        INCOME = "income", "Ingreso"
        EXPENSE = "expense", "Egreso"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    account = models.ForeignKey(
        "accounts.Account",
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.SET_NULL,
        related_name="transactions",
        null=True,
        blank=True,
    )
    kind = models.CharField(max_length=10, choices=Kind.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    date = models.DateField()
    description = models.CharField(max_length=255, blank=True, default="")
    source = models.CharField(max_length=30, blank=True, default="")
    external_reference = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transactions_transaction"
        verbose_name = "transaction"
        verbose_name_plural = "transactions"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["owner", "date"]),
            models.Index(fields=["account", "date"]),
            models.Index(fields=["account", "source", "external_reference"]),
        ]

    def __str__(self) -> str:
        return f"{self.kind} {self.amount} ({self.date})"