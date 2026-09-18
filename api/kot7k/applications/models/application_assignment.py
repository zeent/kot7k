from django.core.exceptions import ValidationError
from django.db import models


class ApplicationAssignment(models.Model):
    application = models.ForeignKey(
        "applications.Application",
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    user = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="application_assignments",
    )
    role = models.ForeignKey(
        "applications.ApplicationRole",
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("application", "user", "role")
        constraints = [
            models.UniqueConstraint(
                fields=("user", "role"),
                name="unique_user_application_role",
            ),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.application_id and self.role_id and self.role.application_id != self.application_id:
            errors["role"] = "The role must belong to the assigned application."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} · {self.application} · {self.role.name}"
