from __future__ import annotations

from django.conf import settings
from django.db import models


class TransferDetectionRule(models.Model):
    class MatchType(models.TextChoices):
        CONTAINS = "contains", "Contiene"
        EQUALS = "equals", "Es igual a"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transfer_detection_rules",
    )
    pattern = models.CharField(max_length=120)
    match_type = models.CharField(max_length=10, choices=MatchType.choices)
    priority = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "transfer_detection_rule"
        verbose_name = "transfer detection rule"
        verbose_name_plural = "transfer detection rules"
        ordering = ["-priority", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "pattern", "match_type"],
                condition=models.Q(is_active=True),
                name="unique_active_transfer_rule_pattern_per_owner",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.pattern} ({self.match_type})"