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


class BootstrapAdminCommandTests(TestCase):
    def test_creates_admin_with_validated_password(self):
        from unittest.mock import patch
        module = "kot7k.authentication.management.commands.bootstrap_admin"
        with patch("builtins.input", side_effect=["NEW@example.com", "Initial Admin"]), patch(
            module + ".getpass", side_effect=["initial-secure-test-981!", "initial-secure-test-981!"]
        ):
            call_command("bootstrap_admin", stdout=StringIO())
        user = get_user_model().objects.get(email="new@example.com")
        self.assertTrue(user.is_superuser and user.is_staff and user.is_active)
        self.assertEqual(user.first_name, "Initial Admin")
        self.assertTrue(user.check_password("initial-secure-test-981!"))

    def test_rerun_does_not_prompt_or_reset_password(self):
        from unittest.mock import patch
        user = get_user_model().objects.create_superuser("admin@example.com", "existing-password")
        with patch("builtins.input") as prompt:
            call_command("bootstrap_admin", stdout=StringIO())
            prompt.assert_not_called()
        user.refresh_from_db()
        self.assertTrue(user.check_password("existing-password"))

    def test_does_not_promote_existing_regular_user(self):
        from unittest.mock import patch
        get_user_model().objects.create_user("user@example.com", "existing-password")
        with patch("builtins.input", side_effect=["user@example.com", "User"]), self.assertRaises(CommandError):
            call_command("bootstrap_admin", stdout=StringIO())
        self.assertFalse(get_user_model().objects.get(email="user@example.com").is_superuser)

    def test_retries_weak_password(self):
        from unittest.mock import patch
        module = "kot7k.authentication.management.commands.bootstrap_admin"
        with patch("builtins.input", side_effect=["new@example.com", "Initial Admin"]), patch(
            module + ".getpass", side_effect=["123", "123", "initial-secure-test-981!", "initial-secure-test-981!"]
        ):
            call_command("bootstrap_admin", stdout=StringIO(), stderr=StringIO())
        self.assertTrue(get_user_model().objects.get(email="new@example.com").check_password("initial-secure-test-981!"))
