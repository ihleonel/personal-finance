from __future__ import annotations

from django.conf import settings
from django.db import models


class CategorizationRule(models.Model):
    class MatchType(models.TextChoices):
        CONTAINS = "contains", "Contiene"
        EQUALS = "equals", "Es igual a"

    class Kind(models.TextChoices):
        INCOME = "income", "Ingreso"
        EXPENSE = "expense", "Egreso"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categorization_rules",
    )
    pattern = models.CharField(max_length=120)
    match_type = models.CharField(max_length=10, choices=MatchType.choices)
    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.CASCADE,
        related_name="categorization_rules",
    )
    kind = models.CharField(max_length=10, choices=Kind.choices)
    priority = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "categorization_rules_rule"
        verbose_name = "categorization rule"
        verbose_name_plural = "categorization rules"
        ordering = ["-priority", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "pattern", "match_type"],
                condition=models.Q(is_active=True),
                name="unique_active_rule_pattern_per_owner",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.pattern} ({self.match_type}) -> {self.category_id}"