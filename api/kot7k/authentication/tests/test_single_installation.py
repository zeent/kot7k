from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from kot7k.organizations.models import IdentityProvider
from kot7k.authentication.models import AccountActivity


class SingleInstallationAuthenticationTests(TestCase):
    def test_password_login_has_no_organization_context(self):
        IdentityProvider.objects.create(key="local", provider_type="local", name="Password", is_enabled=True)
        get_user_model().objects.create_user("person@example.com", "secret-pass")
        response = APIClient().post("/api/authentication/login/", {"email": "person@example.com", "password": "secret-pass"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("organization", response.json()["user"])

    def test_administrator_can_list_users(self):
        admin = get_user_model().objects.create_superuser("admin@example.com", "secret-pass")
        client = APIClient()
        client.force_authenticate(admin)
        response = client.get("/api/authentication/users/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["email"], "admin@example.com")

    def test_logout_is_recorded_for_refresh_token_user(self):
        IdentityProvider.objects.create(
            key="local", provider_type="local", name="Password", is_enabled=True
        )
        user = get_user_model().objects.create_user(
            "person@example.com", "secret-pass"
        )
        client = APIClient()
        login = client.post("/api/authentication/login/", {
            "email": user.email, "password": "secret-pass",
        }, format="json")

        response = client.post("/api/authentication/logout/", {
            "refresh": login.json()["refresh"],
        }, format="json", REMOTE_ADDR="203.0.113.42")

        self.assertEqual(response.status_code, 204)
        self.assertTrue(AccountActivity.objects.filter(
            user=user, action=AccountActivity.Action.LOGOUT,
            ip_address="203.0.113.42",
        ).exists())
