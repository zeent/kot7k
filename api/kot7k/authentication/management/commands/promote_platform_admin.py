from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.db import transaction


class Command(BaseCommand):
    help = "Promote an existing user to KOT7K platform administrator."

    def add_arguments(self, parser):
        parser.add_argument("email")

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        email = User.objects.normalize_email(options["email"].strip()).lower()

        try:
            validate_email(email)
        except ValidationError as exc:
            raise CommandError(f'Invalid email address: "{email}".') from exc

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist as exc:
            raise CommandError(
                f'User with email "{email}" does not exist.'
            ) from exc

        changed_fields = []
        for field in ("is_active", "is_staff", "is_superuser"):
            if not getattr(user, field):
                setattr(user, field, True)
                changed_fields.append(field)

        if changed_fields:
            user.save(update_fields=changed_fields)
            message = f"Promoted {user.email} to platform administrator."
        else:
            message = f"{user.email} is already a platform administrator."

        self.stdout.write(self.style.SUCCESS(message))
