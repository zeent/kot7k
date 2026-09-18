import base64
import json

from django.core.exceptions import ImproperlyConfigured
from webauthn import options_to_json
from webauthn.helpers.structs import AuthenticatorTransport, PublicKeyCredentialDescriptor


def encode_base64url(value):
    return base64.urlsafe_b64encode(bytes(value)).rstrip(b"=").decode("ascii")


def decode_base64url(value):
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def public_options(options):
    return json.loads(options_to_json(options))


def provider_settings(provider):
    configuration = provider.configuration or {}
    rp_id = configuration.get("rp_id")
    origins = configuration.get("origins") or configuration.get("expected_origins")
    if isinstance(origins, str):
        origins = [origins]
    if not rp_id or not origins:
        raise ImproperlyConfigured("WebAuthn requires configuration.rp_id and configuration.origins.")
    return rp_id, configuration.get("rp_name", "KOT7K"), origins


def credential_descriptors(credentials):
    result = []
    for credential in credentials:
        transports = []
        for transport in credential.transports:
            try:
                transports.append(AuthenticatorTransport(transport))
            except ValueError:
                pass
        result.append(PublicKeyCredentialDescriptor(id=decode_base64url(credential.credential_id), transports=transports or None))
    return result
