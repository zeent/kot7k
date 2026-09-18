from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase


class PromotePlatformAdminCommandTests(TestCase):
    def test_promotes_existing_user(self):
        user = get_user_model().objects.create_user(
            email="person@example.com",
            password="strong-test-password",
            is_active=False,
        )

        call_command("promote_platform_admin", user.email)

        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_is_idempotent(self):
        user = get_user_model().objects.create_superuser(
            email="admin@example.com",
            password="strong-test-password",
        )
        output = StringIO()

        call_command("promote_platform_admin", user.email, stdout=output)

        self.assertIn("already a platform administrator", output.getvalue())

    def test_rejects_unknown_user(self):
        with self.assertRaises(CommandError):
            call_command("promote_platform_admin", "missing@example.com")
