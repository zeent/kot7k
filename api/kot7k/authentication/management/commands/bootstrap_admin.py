"""Interactive first administrator; never change credentials on a rerun."""
from getpass import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.db import transaction


class Command(BaseCommand):
    help = "Create the first platform administrator interactively."

    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.filter(is_superuser=True, is_active=True).exists():
            self.stdout.write("An active administrator already exists; credentials unchanged.")
            return
        email = input("Email de l’administrador inicial: ").strip().lower()
        name = input("Nom complet: ").strip()
        try:
            validate_email(email)
        except ValidationError as exc:
            raise CommandError("Email no vàlid.") from exc
        if not name or len(name) > 150:
            raise CommandError("El nom ha de tenir entre 1 i 150 caràcters.")
        if User.objects.filter(email__iexact=email).exists():
            raise CommandError("Aquest usuari ja existeix. Utilitza promote_platform_admin explícitament.")
        user = User(email=email, first_name=name, is_staff=True, is_superuser=True, is_active=True)
        while True:
            password = getpass("Contrasenya: ")
            confirmation = getpass("Repeteix la contrasenya: ")
            if password != confirmation:
                self.stderr.write("Les contrasenyes no coincideixen.")
                continue
            try:
                validate_password(password, user)
            except ValidationError as exc:
                self.stderr.write(" ".join(exc.messages))
                continue
            break
        with transaction.atomic():
            user.set_password(password)
            user.save()
        self.stdout.write(self.style.SUCCESS(f"Administrador creat: {email}"))
