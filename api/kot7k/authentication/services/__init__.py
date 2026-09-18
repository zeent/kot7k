from .google_oidc import (
    GoogleOIDCError,
    build_google_authorization_url,
    exchange_google_code,
    resolve_google_identity,
)
from .microsoft_oidc import (
    MicrosoftOIDCError,
    build_microsoft_authorization_url,
    exchange_microsoft_code,
    resolve_microsoft_identity,
)
from .apple_oidc import (
    AppleOIDCError,
    build_apple_authorization_url,
    exchange_apple_code,
    resolve_apple_identity,
)

__all__ = [
    "GoogleOIDCError",
    "AppleOIDCError",
    "MicrosoftOIDCError",
    "build_google_authorization_url",
    "build_apple_authorization_url",
    "build_microsoft_authorization_url",
    "exchange_google_code",
    "exchange_apple_code",
    "exchange_microsoft_code",
    "resolve_google_identity",
    "resolve_apple_identity",
    "resolve_microsoft_identity",
]
