from django.test import TestCase
from rest_framework.test import APIClient

from kot7k.organizations.models import IdentityProvider
from kot7k.authentication.models import User


class IdentityProviderTests(TestCase):
    def setUp(self):
        IdentityProvider.objects.all().delete()

    def test_discovery_only_returns_enabled_providers(self):
        IdentityProvider.objects.create(key="google", provider_type="google", name="Google", is_enabled=True)
        IdentityProvider.objects.create(key="local", provider_type="local", name="Password", is_enabled=False)
        response = APIClient().get("/api/identity-providers/discovery/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{"key": "google", "provider_type": "google", "name": "Google"}])

    def test_platform_admin_can_manage_an_encrypted_provider_secret(self):
        admin = User.objects.create_superuser("admin@example.com", "password")
        client = APIClient()
        client.force_authenticate(admin)
        response = client.post("/api/identity-providers/", {
            "key": "corporate-google",
            "provider_type": "google",
            "name": "Corporate Google",
            "is_enabled": True,
            "display_order": 1,
            "configuration": {"client_id": "client.apps.googleusercontent.com"},
            "secret": "not-stored-in-clear-text",
        }, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        self.assertNotIn("secret", response.json())
        self.assertTrue(response.json()["has_secret_reference"])
        provider = IdentityProvider.objects.get(key="corporate-google")
        self.assertNotIn("not-stored-in-clear-text", provider.encrypted_secret)
        self.assertEqual(provider.get_secret(), "not-stored-in-clear-text")

    def test_local_provider_connection_can_be_tested(self):
        admin = User.objects.create_superuser("admin@example.com", "password")
        provider = IdentityProvider.objects.create(
            key="local", provider_type="local", name="Local", is_enabled=True
        )
        client = APIClient()
        client.force_authenticate(admin)
        response = client.post(f"/api/identity-providers/{provider.pk}/test/")
        self.assertEqual(response.status_code, 200)
        provider.refresh_from_db()
        self.assertEqual(provider.last_test_status, IdentityProvider.TestStatus.SUCCESS)
        self.assertIsNotNone(provider.last_tested_at)

    def test_ldap_requires_directory_mapping_configuration(self):
        admin = User.objects.create_superuser("admin@example.com", "password")
        client = APIClient()
        client.force_authenticate(admin)
        response = client.post("/api/identity-providers/", {
            "key": "directory", "provider_type": "ldap", "name": "Directory",
            "configuration": {"server_uri": "ldaps://ldap.example.com"},
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("configuration", response.json())


class LocalLoginFallbackTests(TestCase):
    def setUp(self):
        IdentityProvider.objects.all().delete()
        self.user = User.objects.create_superuser("bootstrap@example.com", "local-test-password")
        self.client = APIClient()

    def test_empty_directory_offers_django_login_without_creating_provider(self):
        response = self.client.get("/api/identity-providers/discovery/")
        self.assertEqual(response.json(), [
            {"key": "django-local", "provider_type": "local", "name": "Django"},
        ])
        self.assertFalse(IdentityProvider.objects.exists())
        response = self.client.post("/api/authentication/login/", {
            "email": self.user.email, "password": "local-test-password",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.json())
        self.assertEqual(response.json()["user"]["email"], self.user.email)

    def test_disabled_providers_also_allow_fallback(self):
        IdentityProvider.objects.create(key="disabled", name="Disabled", provider_type="google", is_enabled=False)
        self.assertEqual(self.client.get("/api/identity-providers/discovery/").json()[0]["provider_type"], "local")
        response = self.client.post("/api/authentication/login/", {
            "email": self.user.email, "password": "local-test-password",
        })
        self.assertEqual(response.status_code, 200)

    def test_enabled_external_provider_does_not_enable_local_login(self):
        IdentityProvider.objects.create(key="google", name="Google", provider_type="google", is_enabled=True)
        response = self.client.get("/api/identity-providers/discovery/")
        self.assertEqual([p["provider_type"] for p in response.json()], ["google"])
        response = self.client.post("/api/authentication/login/", {
            "email": self.user.email, "password": "local-test-password",
        })
        self.assertEqual(response.status_code, 403)

    def test_fallback_rejects_wrong_password_and_inactive_user(self):
        for password, active in [("wrong", True), ("local-test-password", False)]:
            with self.subTest(active=active):
                self.user.is_active = active
                self.user.save(update_fields=["is_active"])
                response = self.client.post("/api/authentication/login/", {
                    "email": self.user.email, "password": password,
                })
                self.assertEqual(response.status_code, 401)


class DefaultDjangoProviderTests(TestCase):
    def test_local_login_stays_available_with_microsoft_enabled(self):
        self.assertTrue(IdentityProvider.objects.filter(provider_type="local", is_enabled=True).exists())
        IdentityProvider.objects.create(key="microsoft", name="Microsoft", provider_type="microsoft", is_enabled=True)
        admin = User.objects.create_superuser("local-admin@example.com", "test-local-password")
        client = APIClient()
        types = [p["provider_type"] for p in client.get("/api/identity-providers/discovery/").json()]
        self.assertIn("local", types)
        self.assertIn("microsoft", types)
        response = client.post("/api/authentication/login/", {"email": admin.email, "password": "test-local-password"})
        self.assertEqual(response.status_code, 200)
