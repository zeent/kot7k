from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

provider_key_validator = RegexValidator(
    regex=r"^[a-z0-9](?:[a-z0-9_-]{0,62}[a-z0-9])?$",
    message="Use lowercase letters, numbers, hyphens, and underscores.",
)


class IdentityProvider(models.Model):
    class Type(models.TextChoices):
        LOCAL = "local", "Email and password"
        GOOGLE = "google", "Google"
        MICROSOFT = "microsoft", "Microsoft 365"
        APPLE = "apple", "Apple"
        X509 = "x509", "Digital certificate (X.509/FNMT)"
        WEBAUTHN = "webauthn", "Passkey (WebAuthn)"
        OIDC = "oidc", "OpenID Connect"
        LDAP = "ldap", "LDAP / Active Directory"

    class TestStatus(models.TextChoices):
        NEVER = "never", "Never tested"
        SUCCESS = "success", "Successful"
        ERROR = "error", "Failed"

    key = models.CharField(
        max_length=64,
        unique=True,
        validators=(provider_key_validator,),
        help_text="Stable identifier used in API routes and login screens.",
    )
    provider_type = models.CharField(max_length=16, choices=Type.choices)
    name = models.CharField(max_length=100)
    is_enabled = models.BooleanField(default=False)
    display_order = models.PositiveSmallIntegerField(default=0)
    configuration = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Non-secret provider settings. Store credentials in a secret "
            "manager and reference them with secret_reference."
        ),
    )
    secret_reference = models.CharField(
        max_length=255,
        blank=True,
        help_text="Reference to credentials held outside the database.",
    )
    encrypted_secret = models.TextField(blank=True, editable=False)
    last_tested_at = models.DateTimeField(blank=True, null=True)
    last_test_status = models.CharField(
        max_length=16, choices=TestStatus.choices, default=TestStatus.NEVER
    )
    last_test_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_order", "name", "id")
        indexes = [
            models.Index(
                fields=("is_enabled", "display_order"),
                name="idp_enabled_order_idx",
            ),
        ]

    def clean(self):
        super().clean()
        if not isinstance(self.configuration, dict):
            raise ValidationError(
                {"configuration": "Configuration must be a JSON object."}
            )

    def __str__(self):
        return self.name

    @staticmethod
    def _cipher():
        configured = getattr(settings, "IDENTITY_PROVIDER_ENCRYPTION_KEY", "")
        if configured:
            key = configured.encode()
        else:
            digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
            key = base64.urlsafe_b64encode(digest)
        return Fernet(key)

    def set_secret(self, value):
        self.encrypted_secret = self._cipher().encrypt(value.encode()).decode() if value else ""

    def get_secret(self):
        if not self.encrypted_secret:
            return ""
        try:
            return self._cipher().decrypt(self.encrypted_secret.encode()).decode()
        except InvalidToken as exc:
            raise ValidationError("The identity-provider secret cannot be decrypted.") from exc
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
