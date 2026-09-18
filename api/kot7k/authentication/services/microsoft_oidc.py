import base64
import hashlib
from urllib.parse import urlencode

import jwt
import requests
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.utils import timezone

from kot7k.authentication.models import ExternalIdentity
from kot7k.organizations.services import IdentityProviderConnectionError, resolve_provider_secret


class MicrosoftOIDCError(Exception):
    pass


def _tenant(provider):
    return provider.configuration.get("tenant_id", "organizations").strip()


def _client_id(provider):
    value = provider.configuration.get("client_id", "").strip()
    if not value:
        raise MicrosoftOIDCError("Microsoft client_id is not configured.")
    return value


def _client_secret(provider):
    try:
        return resolve_provider_secret(provider)
    except IdentityProviderConnectionError as exc:
        raise MicrosoftOIDCError("Microsoft client secret is not available.") from exc


def build_microsoft_authorization_url(
    provider, redirect_uri, state, nonce, verifier
):
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    query = urlencode(
        {
            "client_id": _client_id(provider),
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "response_mode": "query",
            "scope": "openid profile email",
            "state": state,
            "nonce": nonce,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
    )
    return (
        f"https://login.microsoftonline.com/{_tenant(provider)}"
        f"/oauth2/v2.0/authorize?{query}"
    )


def exchange_microsoft_code(provider, code, redirect_uri, verifier, nonce):
    tenant = _tenant(provider)
    try:
        response = requests.post(
            f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
            data={
                "client_id": _client_id(provider),
                "client_secret": _client_secret(provider),
                "code": code,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
                "code_verifier": verifier,
            },
            timeout=10,
        )
        response.raise_for_status()
        raw_token = response.json()["id_token"]
        unverified = jwt.decode(
            raw_token,
            options={"verify_signature": False},
            algorithms=["RS256"],
        )
        token_tenant = unverified["tid"]
        configured_tenants = provider.configuration.get("allowed_tenant_ids", [])
        if configured_tenants and token_tenant not in configured_tenants:
            raise MicrosoftOIDCError("This Microsoft tenant is not allowed.")
        if tenant not in {"common", "organizations", "consumers"} and token_tenant != tenant:
            raise MicrosoftOIDCError("The Microsoft tenant does not match.")

        signing_key = jwt.PyJWKClient(
            f"https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys"
        ).get_signing_key_from_jwt(raw_token)
        claims = jwt.decode(
            raw_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=_client_id(provider),
            issuer=f"https://login.microsoftonline.com/{token_tenant}/v2.0",
        )
    except MicrosoftOIDCError:
        raise
    except (requests.RequestException, KeyError, ValueError, jwt.PyJWTError) as exc:
        raise MicrosoftOIDCError(
            "Microsoft authentication could not be verified."
        ) from exc

    if claims.get("nonce") != nonce:
        raise MicrosoftOIDCError("Microsoft authentication nonce is invalid.")
    return claims


@transaction.atomic
def resolve_microsoft_identity(provider, claims):
    tenant_id = claims.get("tid", "")
    object_id = claims.get("oid") or claims.get("sub", "")
    subject = f"{tenant_id}:{object_id}"
    email = (claims.get("email") or claims.get("preferred_username") or "").strip().lower()
    if not tenant_id or not object_id or not email:
        raise MicrosoftOIDCError("Microsoft did not return a usable identity.")

    try:
        validate_email(email)
    except ValidationError as exc:
        raise MicrosoftOIDCError("Microsoft did not return a usable email address.") from exc

    allowed_domains = provider.configuration.get("allowed_domains", [])
    email_domain = email.rsplit("@", 1)[-1]
    if allowed_domains and email_domain not in {domain.lower() for domain in allowed_domains}:
        raise MicrosoftOIDCError("This Microsoft email domain is not allowed.")

    identity = ExternalIdentity.objects.select_related("user").filter(
        provider=provider,
        subject=subject,
    ).first()
    if identity:
        if not identity.user.is_active:
            raise MicrosoftOIDCError("Active user account required.")
        identity.email = email
        identity.last_login_at = timezone.now()
        identity.save(update_fields=("email", "last_login_at", "updated_at"))
        return identity.user

    User = get_user_model()
    user, _ = User.objects.get_or_create(
        email=email,
        defaults={
            "password": make_password(None),
            "first_name": str(claims.get("given_name") or "")[:150],
            "last_name": str(claims.get("family_name") or "")[:150],
            "is_active": True,
            "is_staff": False,
            "is_superuser": False,
        },
    )
    if not user.is_active:
        raise MicrosoftOIDCError("Active user account required.")
    if ExternalIdentity.objects.filter(provider=provider, user=user).exists():
        raise MicrosoftOIDCError("This account is already linked to another Microsoft identity.")

    ExternalIdentity.objects.create(
        provider=provider,
        user=user,
        subject=subject,
        email=email,
        last_login_at=timezone.now(),
    )
    return user
