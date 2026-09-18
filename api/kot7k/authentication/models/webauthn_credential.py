from django.conf import settings
from django.db import models


class WebAuthnCredential(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="webauthn_credentials")
    provider = models.ForeignKey("organizations.IdentityProvider", on_delete=models.CASCADE, related_name="webauthn_credentials")
    credential_id = models.CharField(max_length=1400)
    public_key = models.BinaryField()
    sign_count = models.PositiveBigIntegerField(default=0)
    transports = models.JSONField(default=list, blank=True)
    name = models.CharField(max_length=100, default="Passkey")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [models.UniqueConstraint(fields=("provider", "credential_id"), name="unique_webauthn_provider_credential")]
        indexes = [models.Index(fields=("provider", "user"), name="webauthn_provider_user_idx")]

    def __str__(self):
        return f"{self.user} · {self.name}"
