import base64
import hashlib
from urllib.parse import urlencode

import requests
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from kot7k.authentication.models import ExternalIdentity
from kot7k.organizations.services import IdentityProviderConnectionError, resolve_provider_secret


GOOGLE_AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"


class GoogleOIDCError(Exception):
    pass


def _resolve_client_secret(provider):
    try:
        return resolve_provider_secret(provider)
    except IdentityProviderConnectionError as exc:
        raise GoogleOIDCError("Google client secret is not available.") from exc


def _client_id(provider):
    client_id = provider.configuration.get("client_id", "").strip()
    if not client_id:
        raise GoogleOIDCError("Google client_id is not configured.")
    return client_id


def build_google_authorization_url(provider, redirect_uri, state, nonce, verifier):
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    parameters = {
        "client_id": _client_id(provider),
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "nonce": nonce,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    hosted_domains = provider.configuration.get("allowed_domains", [])
    if len(hosted_domains) == 1:
        parameters["hd"] = hosted_domains[0]
    return f"{GOOGLE_AUTHORIZATION_ENDPOINT}?{urlencode(parameters)}"


def exchange_google_code(provider, code, redirect_uri, verifier, nonce):
    try:
        response = requests.post(
            GOOGLE_TOKEN_ENDPOINT,
            data={
                "code": code,
                "client_id": _client_id(provider),
                "client_secret": _resolve_client_secret(provider),
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
                "code_verifier": verifier,
            },
            timeout=10,
        )
        response.raise_for_status()
        raw_id_token = response.json()["id_token"]
        claims = id_token.verify_oauth2_token(
            raw_id_token,
            google_requests.Request(),
            _client_id(provider),
        )
    except (requests.RequestException, KeyError, ValueError) as exc:
        raise GoogleOIDCError(
            "Google authentication could not be verified."
        ) from exc

    if claims.get("nonce") != nonce:
        raise GoogleOIDCError("Google authentication nonce is invalid.")
    if not claims.get("email_verified"):
        raise GoogleOIDCError("Google has not verified this email address.")

    allowed_domains = provider.configuration.get("allowed_domains", [])
    if allowed_domains and claims.get("hd") not in allowed_domains:
        raise GoogleOIDCError("This Google domain is not allowed.")
    return claims


@transaction.atomic
def resolve_google_identity(provider, claims):
    subject = claims.get("sub", "")
    email = claims.get("email", "").strip().lower()
    if not subject or not email:
        raise GoogleOIDCError("Google did not return a usable identity.")

    identity = ExternalIdentity.objects.select_related("user").filter(
        provider=provider,
        subject=subject,
    ).first()
    if identity is not None:
        identity.email = email
        identity.last_login_at = timezone.now()
        identity.save(update_fields=("email", "last_login_at", "updated_at"))
        return identity.user

    authoritative = email.endswith("@gmail.com") or bool(claims.get("hd"))
    if not authoritative:
        raise GoogleOIDCError(
            "This Google account cannot be linked automatically by email."
        )

    User = get_user_model()
    user = User.objects.filter(email=email, is_active=True).first()
    if user is None:
        raise GoogleOIDCError(
            "No active account matches this Google user."
        )

    ExternalIdentity.objects.create(
        provider=provider,
        user=user,
        subject=subject,
        email=email,
        last_login_at=timezone.now(),
    )
    return user
