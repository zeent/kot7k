from django.conf import settings
from django.db import models


class ExternalIdentity(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="external_identities",
    )
    provider = models.ForeignKey(
        "organizations.IdentityProvider",
        on_delete=models.CASCADE,
        related_name="external_identities",
    )
    subject = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("provider", "user")
        constraints = [
            models.UniqueConstraint(
                fields=("provider", "subject"),
                name="unique_provider_subject",
            ),
            models.UniqueConstraint(
                fields=("provider", "user"),
                name="unique_provider_user",
            ),
        ]

    def __str__(self):
        return f"{self.provider} · {self.user}"
