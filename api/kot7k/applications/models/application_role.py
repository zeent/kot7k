from django.db import models

from .application import application_key_validator


class ApplicationRole(models.Model):
    application = models.ForeignKey(
        "applications.Application",
        on_delete=models.CASCADE,
        related_name="roles",
    )
    key = models.CharField(max_length=64, validators=(application_key_validator,))
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("application", "name", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("application", "key"),
                name="unique_application_role_key",
            ),
        ]

    def __str__(self):
        return f"{self.application} · {self.name}"
