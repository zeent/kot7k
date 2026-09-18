import os

import requests
from ldap3 import Connection, Server, Tls

from kot7k.organizations.models import IdentityProvider


class IdentityProviderConnectionError(Exception):
    pass


def resolve_provider_secret(provider):
    if provider.encrypted_secret:
        return provider.get_secret()
    reference = provider.secret_reference
    if reference.startswith("env://"):
        value = os.getenv(reference.removeprefix("env://"), "")
        if value:
            return value.replace("\\n", "\n")
    raise IdentityProviderConnectionError("The provider secret is not configured.")


def _fetch_discovery(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        document = response.json()
        if not document.get("authorization_endpoint") or not document.get("token_endpoint"):
            raise IdentityProviderConnectionError("The discovery document is incomplete.")
        return "OpenID Connect discovery completed successfully."
    except (requests.RequestException, ValueError) as exc:
        raise IdentityProviderConnectionError("Could not load the OpenID Connect discovery document.") from exc


def test_provider(provider):
    config = provider.configuration
    if provider.provider_type == IdentityProvider.Type.LOCAL:
        return "Local authentication is available."
    if provider.provider_type == IdentityProvider.Type.WEBAUTHN:
        return "The WebAuthn relying-party configuration is valid."
    if provider.provider_type == IdentityProvider.Type.X509:
        return "The X.509 proxy-header configuration is valid."
    if provider.provider_type == IdentityProvider.Type.GOOGLE:
        resolve_provider_secret(provider)
        return _fetch_discovery("https://accounts.google.com/.well-known/openid-configuration")
    if provider.provider_type == IdentityProvider.Type.MICROSOFT:
        resolve_provider_secret(provider)
        tenant = config.get("tenant_id", "organizations")
        return _fetch_discovery(
            f"https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid-configuration"
        )
    if provider.provider_type == IdentityProvider.Type.APPLE:
        resolve_provider_secret(provider)
        return _fetch_discovery("https://appleid.apple.com/.well-known/openid-configuration")
    if provider.provider_type == IdentityProvider.Type.OIDC:
        resolve_provider_secret(provider)
        issuer = str(config["issuer"]).rstrip("/")
        return _fetch_discovery(f"{issuer}/.well-known/openid-configuration")
    if provider.provider_type == IdentityProvider.Type.LDAP:
        secret = resolve_provider_secret(provider)
        uri = str(config["server_uri"])
        use_ssl = uri.lower().startswith("ldaps://")
        host = uri.split("://", 1)[-1].split(":", 1)[0]
        port = int(config.get("port") or (636 if use_ssl else 389))
        try:
            server = Server(host, port=port, use_ssl=use_ssl, connect_timeout=10, tls=Tls())
            connection = Connection(
                server, user=config.get("bind_dn", ""), password=secret,
                auto_bind=True, receive_timeout=10,
            )
            connection.unbind()
            return "LDAP bind completed successfully."
        except Exception as exc:
            raise IdentityProviderConnectionError("Could not connect or bind to the LDAP directory.") from exc
    raise IdentityProviderConnectionError("This provider type cannot be tested.")
