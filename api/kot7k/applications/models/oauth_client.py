import secrets

from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.db import models


def generate_client_id():
    return secrets.token_urlsafe(32)


def default_allowed_scopes():
    return ["openid", "profile", "email", "roles", "offline_access"]


class OAuthClient(models.Model):
    application = models.OneToOneField(
        "applications.Application", on_delete=models.CASCADE, related_name="oauth_client"
    )
    client_id = models.CharField(max_length=255, unique=True, default=generate_client_id)
    client_secret_hash = models.CharField(max_length=255, blank=True)
    is_confidential = models.BooleanField(default=True)
    redirect_uris = models.JSONField(default=list)
    backchannel_logout_uri = models.URLField(max_length=2048, blank=True)
    post_logout_redirect_uris = models.JSONField(default=list, blank=True)
    allowed_scopes = models.JSONField(default=default_allowed_scopes)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("application__name",)

    def clean(self):
        super().clean()
        if not isinstance(self.redirect_uris, list) or not all(
            isinstance(uri, str) and uri for uri in self.redirect_uris
        ):
            raise ValidationError({"redirect_uris": "Use a list of absolute redirect URIs."})
        from kot7k.authentication.services.sso import validate_logout_uri
        if self.backchannel_logout_uri:
            validate_logout_uri(self.backchannel_logout_uri)
        if not isinstance(self.post_logout_redirect_uris, list):
            raise ValidationError({"post_logout_redirect_uris": "Use a list of URIs."})
        for uri in self.post_logout_redirect_uris:
            validate_logout_uri(uri)
        if not isinstance(self.allowed_scopes, list) or "openid" not in self.allowed_scopes:
            raise ValidationError({"allowed_scopes": "The openid scope is required."})

    def set_secret(self, raw_secret):
        self.client_secret_hash = make_password(raw_secret)

    def check_secret(self, raw_secret):
        return bool(self.client_secret_hash and check_password(raw_secret, self.client_secret_hash))

    def __str__(self):
        return f"{self.application} · {self.client_id}"
