import base64
import hashlib
import os
import re
import secrets
from datetime import timedelta

import jwt
from cryptography.hazmat.primitives import serialization
from django.conf import settings
from django.utils import timezone

from kot7k.applications.models import ApplicationAssignment, OAuthRefreshToken


class OIDCProviderError(Exception):
    pass


def issuer():
    return settings.OIDC_ISSUER.rstrip("/")


def _private_key():
    value = os.getenv(settings.OIDC_PRIVATE_KEY_ENV, "").replace("\\n", "\n")
    if not value:
        raise OIDCProviderError(f"{settings.OIDC_PRIVATE_KEY_ENV} is not configured.")
    return value


def _public_key_object():
    configured = os.getenv(settings.OIDC_PUBLIC_KEY_ENV, "").replace("\\n", "\n")
    if configured:
        return serialization.load_pem_public_key(configured.encode())
    private = serialization.load_pem_private_key(_private_key().encode(), password=None)
    return private.public_key()


def _base64url_uint(value):
    size = (value.bit_length() + 7) // 8
    return base64.urlsafe_b64encode(value.to_bytes(size, "big")).rstrip(b"=").decode()


def jwks_document():
    numbers = _public_key_object().public_numbers()
    return {"keys": [{
        "kty": "RSA", "use": "sig", "alg": "RS256", "kid": settings.OIDC_KEY_ID,
        "n": _base64url_uint(numbers.n), "e": _base64url_uint(numbers.e),
    }]}


def hash_token(raw):
    return hashlib.sha256(raw.encode()).hexdigest()


def verify_pkce(verifier, challenge):
    if not re.fullmatch(r"[A-Za-z0-9._~-]{43,128}", verifier):
        return False
    calculated = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return secrets.compare_digest(calculated, challenge)


def user_roles(user, application):
    return list(ApplicationAssignment.objects.filter(
        user=user, application=application
    ).values_list("role__key", flat=True).distinct())


def _common_claims(user, client, token_use, lifetime):
    now = timezone.now()
    return {
        "iss": issuer(),
        "sub": str(user.oidc_subject),
        "aud": client.client_id,
        "iat": int(now.timestamp()),
        "exp": int((now + lifetime).timestamp()),
        "jti": secrets.token_urlsafe(24),
        "token_use": token_use,
    }


def _sign(claims):
    return jwt.encode(
        claims, _private_key(), algorithm="RS256", headers={"kid": settings.OIDC_KEY_ID}
    )


def issue_tokens(user, client, scopes, nonce=None, include_refresh=True, session=None):
    from .sso import active_session
    from kot7k.authentication.models import SessionApplication
    if session is None or not active_session(session.pk, user.pk):
        raise OIDCProviderError("Session expired or signed out.")
    SessionApplication.objects.get_or_create(session=session, client=client)
    roles = user_roles(user, client.application)
    access_claims = _common_claims(
        user, client, "access", timedelta(seconds=settings.OIDC_ACCESS_TOKEN_LIFETIME)
    )
    access_claims["sid"] = str(session.pk)
    access_claims.update({"scope": " ".join(scopes), "roles": roles})
    access_token = _sign(access_claims)

    id_claims = _common_claims(
        user, client, "id", timedelta(seconds=settings.OIDC_ID_TOKEN_LIFETIME)
    )
    id_claims.update({
        "email": user.email,
        "email_verified": True,
        "name": user.get_full_name(),
        "given_name": user.first_name,
        "family_name": user.last_name,
        "roles": roles,
    })
    id_claims["sid"] = str(session.pk)
    if nonce:
        id_claims["nonce"] = nonce

    response = {
        "access_token": access_token,
        "id_token": _sign(id_claims),
        "token_type": "Bearer",
        "expires_in": settings.OIDC_ACCESS_TOKEN_LIFETIME,
        "scope": " ".join(scopes),
    }
    if include_refresh:
        raw_refresh = secrets.token_urlsafe(64)
        OAuthRefreshToken.objects.create(
            token_hash=hash_token(raw_refresh), client=client, user=user, scopes=scopes, session=session,
            expires_at=timezone.now() + timedelta(seconds=settings.OIDC_REFRESH_TOKEN_LIFETIME),
        )
        response["refresh_token"] = raw_refresh
    return response


def decode_access_token(raw_token):
    try:
        header = jwt.get_unverified_header(raw_token)
        if header.get("kid") != settings.OIDC_KEY_ID:
            raise OIDCProviderError("Unknown signing key.")
        claims = jwt.decode(
            raw_token,
            _public_key_object(),
            algorithms=["RS256"],
            issuer=issuer(),
            options={"verify_aud": False},
        )
        from .sso import active_session
        if not active_session(claims.get("sid")):
            raise OIDCProviderError("Session expired or signed out.")
        return claims
    except (jwt.PyJWTError, ValueError, TypeError) as exc:
        raise OIDCProviderError("Invalid access token.") from exc
