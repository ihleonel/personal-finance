from __future__ import annotations

from django.conf import settings
from django.db import models


class Category(models.Model):
    class Kind(models.TextChoices):
        INCOME = "income", "Ingreso"
        EXPENSE = "expense", "Egreso"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=10, choices=Kind.choices)
    include_in_summaries = models.BooleanField(default=True)
    is_fixed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "categories_category"
        verbose_name = "category"
        verbose_name_plural = "categories"
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name"],
                condition=models.Q(is_active=True),
                name="unique_active_category_name_per_owner",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.kind})"