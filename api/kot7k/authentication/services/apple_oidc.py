import time
from urllib.parse import urlencode

import jwt
import requests
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from kot7k.authentication.models import ExternalIdentity
from kot7k.organizations.services import IdentityProviderConnectionError, resolve_provider_secret


APPLE_AUTHORIZATION_ENDPOINT = "https://appleid.apple.com/auth/authorize"
APPLE_TOKEN_ENDPOINT = "https://appleid.apple.com/auth/token"
APPLE_KEYS_ENDPOINT = "https://appleid.apple.com/auth/keys"
APPLE_ISSUER = "https://appleid.apple.com"


class AppleOIDCError(Exception):
    pass


def _setting(provider, key):
    value = str(provider.configuration.get(key, "")).strip()
    if not value:
        raise AppleOIDCError(f"Apple {key} is not configured.")
    return value


def _private_key(provider):
    try:
        return resolve_provider_secret(provider)
    except IdentityProviderConnectionError as exc:
        raise AppleOIDCError("Apple private key is not available.") from exc


def create_apple_client_secret(provider):
    now = int(time.time())
    return jwt.encode(
        {
            "iss": _setting(provider, "team_id"),
            "iat": now,
            "exp": now + 300,
            "aud": APPLE_ISSUER,
            "sub": _setting(provider, "client_id"),
        },
        _private_key(provider),
        algorithm="ES256",
        headers={"kid": _setting(provider, "key_id")},
    )


def build_apple_authorization_url(provider, redirect_uri, state, nonce):
    return f"{APPLE_AUTHORIZATION_ENDPOINT}?{urlencode({
        'client_id': _setting(provider, 'client_id'),
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'response_mode': 'form_post',
        'scope': 'name email',
        'state': state,
        'nonce': nonce,
    })}"


def exchange_apple_code(provider, code, redirect_uri, nonce):
    try:
        response = requests.post(
            APPLE_TOKEN_ENDPOINT,
            data={
                "client_id": _setting(provider, "client_id"),
                "client_secret": create_apple_client_secret(provider),
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
            timeout=10,
        )
        response.raise_for_status()
        raw_token = response.json()["id_token"]
        signing_key = jwt.PyJWKClient(APPLE_KEYS_ENDPOINT).get_signing_key_from_jwt(raw_token)
        claims = jwt.decode(
            raw_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=_setting(provider, "client_id"),
            issuer=APPLE_ISSUER,
        )
    except AppleOIDCError:
        raise
    except (requests.RequestException, KeyError, ValueError, jwt.PyJWTError) as exc:
        raise AppleOIDCError("Apple authentication could not be verified.") from exc

    if claims.get("nonce") != nonce:
        raise AppleOIDCError("Apple authentication nonce is invalid.")
    if str(claims.get("email_verified", "")).lower() != "true":
        raise AppleOIDCError("Apple has not verified this email address.")
    return claims


@transaction.atomic
def resolve_apple_identity(provider, claims):
    subject = claims.get("sub", "")
    email = claims.get("email", "").strip().lower()
    if not subject or not email:
        raise AppleOIDCError("Apple did not return a usable identity.")

    identity = ExternalIdentity.objects.select_related("user").filter(
        provider=provider, subject=subject
    ).first()
    if identity:
        identity.email = email
        identity.last_login_at = timezone.now()
        identity.save(update_fields=("email", "last_login_at", "updated_at"))
        return identity.user

    allowed_domains = provider.configuration.get("allowed_domains", [])
    if allowed_domains and email.rsplit("@", 1)[-1] not in allowed_domains:
        raise AppleOIDCError("This Apple email domain is not allowed.")

    user = get_user_model().objects.filter(email=email, is_active=True).first()
    if user is None:
        raise AppleOIDCError("No active account matches this Apple user.")
    ExternalIdentity.objects.create(
        provider=provider,
        user=user,
        subject=subject,
        email=email,
        last_login_at=timezone.now(),
    )
    return user
