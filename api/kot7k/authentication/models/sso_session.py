import uuid
from django.conf import settings
from django.db import models


class SSOSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    provider_type = models.CharField(max_length=20, default="local")
    provider_key = models.CharField(max_length=64, blank=True)
    django_session_key = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)


class SessionApplication(models.Model):
    session = models.ForeignKey(SSOSession, on_delete=models.CASCADE, related_name="applications")
    client = models.ForeignKey("applications.OAuthClient", on_delete=models.CASCADE)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("session", "client"), name="unique_sso_session_client")]


class LogoutDelivery(models.Model):
    session = models.ForeignKey(SSOSession, on_delete=models.CASCADE)
    client = models.ForeignKey("applications.OAuthClient", on_delete=models.CASCADE)
    endpoint = models.URLField(max_length=2048)
    attempts = models.PositiveIntegerField(default=0)
    delivered_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("session", "client"), name="unique_sso_logout_delivery")]
