from pathlib import Path

from cryptography import x509
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from kot7k.authentication.models import ExternalIdentity
from kot7k.authentication.services.x509 import certificate_subject
from kot7k.organizations.models import IdentityProvider


class Command(BaseCommand):
    help = "Link an X.509 certificate to an existing user."

    def add_arguments(self, parser):
        parser.add_argument("provider")
        parser.add_argument("email")
        parser.add_argument("certificate")

    def handle(self, *args, **options):
        try:
            provider = IdentityProvider.objects.get(
                key=options["provider"],
                provider_type=IdentityProvider.Type.X509,
            )
            user = get_user_model().objects.get(email=options["email"].lower())
            if not user.is_active:
                raise get_user_model().DoesNotExist
            certificate = x509.load_pem_x509_certificate(
                Path(options["certificate"]).read_bytes()
            )
        except IdentityProvider.DoesNotExist as exc:
            raise CommandError("X.509 provider not found.") from exc
        except get_user_model().DoesNotExist as exc:
            raise CommandError("Active user not found.") from exc
        except (OSError, ValueError) as exc:
            raise CommandError("Certificate could not be read as PEM.") from exc

        identity, created = ExternalIdentity.objects.update_or_create(
            provider=provider,
            subject=certificate_subject(certificate),
            defaults={"user": user},
        )
        action = "Linked" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} certificate to {identity.user}."))
