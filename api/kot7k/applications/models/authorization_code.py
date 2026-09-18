from django.conf import settings
from django.db import models


class AuthorizationCode(models.Model):
    code_hash = models.CharField(max_length=64, unique=True)
    client = models.ForeignKey("applications.OAuthClient", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    redirect_uri = models.TextField()
    session = models.ForeignKey("authentication.SSOSession", null=True, blank=True, on_delete=models.CASCADE)
    scopes = models.JSONField(default=list)
    nonce = models.CharField(max_length=255)
    code_challenge = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=("code_hash", "expires_at"), name="oidc_code_expiry_idx")]
