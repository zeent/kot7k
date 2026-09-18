from django.core.management.base import BaseCommand
from kot7k.authentication.services.sso import deliver_pending


class Command(BaseCommand):
    help = "Retry pending OIDC back-channel logout notifications. Schedule in production."

    def handle(self, *args, **options):
        self.stdout.write(f"Delivered: {deliver_pending()}")
