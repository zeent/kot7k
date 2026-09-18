from django.conf import settings
from django.db import models


class OAuthRefreshToken(models.Model):
    token_hash = models.CharField(max_length=64, unique=True)
    client = models.ForeignKey("applications.OAuthClient", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session = models.ForeignKey("authentication.SSOSession", null=True, blank=True, on_delete=models.CASCADE)
    scopes = models.JSONField(default=list)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=("token_hash", "expires_at"), name="oidc_refresh_expiry_idx")]
