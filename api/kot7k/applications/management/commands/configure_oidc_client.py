import secrets

from django.core.management.base import BaseCommand, CommandError

from kot7k.applications.models import Application, OAuthClient


class Command(BaseCommand):
    help = "Create or update the OpenID Connect client for an application."

    def add_arguments(self, parser):
        parser.add_argument("application_key")
        parser.add_argument("--redirect-uri", action="append", required=True)
        parser.add_argument("--client-id")
        parser.add_argument("--backchannel-logout-uri")
        parser.add_argument("--post-logout-redirect-uri", action="append")
        parser.add_argument("--public", action="store_true", dest="is_public")
        parser.add_argument("--rotate-secret", action="store_true")

    def handle(self, *args, **options):
        try:
            application = Application.objects.get(key=options["application_key"])
        except Application.DoesNotExist as exc:
            raise CommandError("Application not found.") from exc

        client, created = OAuthClient.objects.get_or_create(
            application=application,
            defaults={"client_id": options["client_id"] or secrets.token_urlsafe(32)},
        )
        if options["client_id"]:
            client.client_id = options["client_id"]
        client.redirect_uris = list(dict.fromkeys(options["redirect_uri"]))
        if options["backchannel_logout_uri"] is not None:
            client.backchannel_logout_uri = options["backchannel_logout_uri"]
        if options["post_logout_redirect_uri"] is not None:
            client.post_logout_redirect_uris = options["post_logout_redirect_uri"]
        client.is_confidential = not options["is_public"]

        raw_secret = None
        if client.is_confidential and (created or options["rotate_secret"] or not client.client_secret_hash):
            raw_secret = secrets.token_urlsafe(48)
            client.set_secret(raw_secret)
        if not client.is_confidential:
            client.client_secret_hash = ""
        client.full_clean()
        client.save()

        self.stdout.write(self.style.SUCCESS(f"OIDC client configured for {application.key}."))
        self.stdout.write(f"Client ID: {client.client_id}")
        if raw_secret:
            self.stdout.write(self.style.WARNING(f"Client secret (shown once): {raw_secret}"))
