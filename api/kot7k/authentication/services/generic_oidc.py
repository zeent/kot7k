import base64
import hashlib
from urllib.parse import urlencode

import jwt
import requests
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from kot7k.authentication.models import ExternalIdentity
from kot7k.organizations.services import IdentityProviderConnectionError, resolve_provider_secret


class GenericOIDCError(Exception):
    pass


def _discovery(provider):
    issuer = str(provider.configuration.get("issuer", "")).rstrip("/")
    if not issuer:
        raise GenericOIDCError("The OpenID Connect issuer is not configured.")
    try:
        response = requests.get(f"{issuer}/.well-known/openid-configuration", timeout=10)
        response.raise_for_status()
        document = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise GenericOIDCError("OpenID Connect discovery failed.") from exc
    if document.get("issuer", "").rstrip("/") != issuer:
        raise GenericOIDCError("The discovered issuer does not match the configured issuer.")
    return document


def _client_id(provider):
    value = str(provider.configuration.get("client_id", "")).strip()
    if not value:
        raise GenericOIDCError("The OpenID Connect client ID is not configured.")
    return value


def build_authorization_url(provider, redirect_uri, state, nonce, verifier):
    document = _discovery(provider)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    scopes = provider.configuration.get("scopes") or ["openid", "email", "profile"]
    return f"{document['authorization_endpoint']}?{urlencode({
        'client_id': _client_id(provider), 'redirect_uri': redirect_uri,
        'response_type': 'code', 'scope': ' '.join(scopes), 'state': state,
        'nonce': nonce, 'code_challenge': challenge, 'code_challenge_method': 'S256',
    })}"


def exchange_code(provider, code, redirect_uri, verifier, nonce):
    document = _discovery(provider)
    try:
        secret = resolve_provider_secret(provider)
        response = requests.post(document["token_endpoint"], data={
            "client_id": _client_id(provider), "client_secret": secret, "code": code,
            "redirect_uri": redirect_uri, "grant_type": "authorization_code", "code_verifier": verifier,
        }, timeout=10)
        response.raise_for_status()
        raw_token = response.json()["id_token"]
        signing_key = jwt.PyJWKClient(document["jwks_uri"]).get_signing_key_from_jwt(raw_token)
        claims = jwt.decode(raw_token, signing_key.key, algorithms=["RS256", "ES256"],
                            audience=_client_id(provider), issuer=document["issuer"])
    except (IdentityProviderConnectionError, requests.RequestException, KeyError, ValueError, jwt.PyJWTError) as exc:
        raise GenericOIDCError("OpenID Connect authentication could not be verified.") from exc
    if claims.get("nonce") != nonce:
        raise GenericOIDCError("The OpenID Connect nonce is invalid.")
    return claims


@transaction.atomic
def resolve_identity(provider, claims):
    subject = str(claims.get("sub", ""))
    email = str(claims.get("email", "")).strip().lower()
    if not subject or not email or claims.get("email_verified") is not True:
        raise GenericOIDCError("The provider did not return a verified email address.")
    allowed = provider.configuration.get("allowed_domains", [])
    if allowed and email.rsplit("@", 1)[-1] not in allowed:
        raise GenericOIDCError("This email domain is not allowed.")
    identity = ExternalIdentity.objects.select_related("user").filter(provider=provider, subject=subject).first()
    if identity:
        identity.email = email; identity.last_login_at = timezone.now()
        identity.save(update_fields=("email", "last_login_at", "updated_at"))
        return identity.user
    user = get_user_model().objects.filter(email=email, is_active=True).first()
    if user is None:
        raise GenericOIDCError("No active account matches this identity.")
    ExternalIdentity.objects.create(provider=provider, user=user, subject=subject, email=email, last_login_at=timezone.now())
    return user
