import hashlib
from datetime import datetime, timezone
from urllib.parse import unquote

from cryptography import x509
from cryptography.x509.oid import NameOID
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone as django_timezone

from kot7k.authentication.models import ExternalIdentity


class X509AuthenticationError(Exception):
    pass


def load_verified_client_certificate(request):
    if request.META.get("REMOTE_ADDR") not in request.x509_trusted_proxy_ips:
        raise X509AuthenticationError("The certificate proxy is not trusted.")
    if request.META.get("HTTP_X_SSL_CLIENT_VERIFY") != "SUCCESS":
        raise X509AuthenticationError("A valid client certificate is required.")
    encoded_certificate = request.META.get("HTTP_X_SSL_CLIENT_CERT", "")
    try:
        certificate = x509.load_pem_x509_certificate(
            unquote(encoded_certificate).encode()
        )
    except (TypeError, ValueError) as exc:
        raise X509AuthenticationError("The client certificate is invalid.") from exc

    now = datetime.now(timezone.utc)
    if not certificate.not_valid_before_utc <= now <= certificate.not_valid_after_utc:
        raise X509AuthenticationError("The client certificate has expired.")
    return certificate


def certificate_subject(certificate):
    attributes = certificate.subject.get_attributes_for_oid(NameOID.SERIAL_NUMBER)
    person_identifier = attributes[0].value if attributes else None
    stable_value = person_identifier or format(certificate.serial_number, "x")
    canonical = f"{certificate.issuer.rfc4514_string()}|{stable_value}"
    return hashlib.sha256(canonical.encode()).hexdigest()


def certificate_email(certificate):
    try:
        names = certificate.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        ).value.get_values_for_type(x509.RFC822Name)
    except x509.ExtensionNotFound:
        names = []
    return names[0].strip().lower() if names else ""


@transaction.atomic
def resolve_x509_identity(provider, certificate):
    issuer = certificate.issuer.rfc4514_string()
    allowed_issuers = provider.configuration.get("allowed_issuer_contains", [])
    if allowed_issuers and not any(value in issuer for value in allowed_issuers):
        raise X509AuthenticationError("This certificate issuer is not allowed.")

    subject = certificate_subject(certificate)
    email = certificate_email(certificate)
    identity = ExternalIdentity.objects.select_related("user").filter(
        provider=provider, subject=subject
    ).first()
    if identity:
        identity.email = email
        identity.last_login_at = django_timezone.now()
        identity.save(update_fields=("email", "last_login_at", "updated_at"))
        return identity.user

    if not email:
        raise X509AuthenticationError(
            "This certificate must be linked to a user by an administrator."
        )
    User = get_user_model()
    user = User.objects.filter(email=email, is_active=True).first()
    if user is None:
        raise X509AuthenticationError(
            "No active account matches this certificate."
        )
    ExternalIdentity.objects.create(
        provider=provider,
        user=user,
        subject=subject,
        email=email,
        last_login_at=django_timezone.now(),
    )
    return user
