from django.contrib.auth import get_user_model
from django.test import TestCase
from kot7k.authentication.models import ExternalIdentity
from kot7k.applications.models import ApplicationAssignment
from kot7k.authentication.services.microsoft_oidc import MicrosoftOIDCError, resolve_microsoft_identity
from kot7k.organizations.models import IdentityProvider


class MicrosoftProvisioningTests(TestCase):
    def setUp(self):
        self.provider = IdentityProvider.objects.create(key="entra", name="Entra", provider_type="microsoft", is_enabled=True, configuration={"allowed_domains": ["example.com"]})
        self.claims = {"tid": "tenant", "oid": "object", "email": "Person@Example.com", "given_name": "Joan", "family_name": "Camps"}

    def test_creates_regular_user_and_reuses_identity(self):
        user = resolve_microsoft_identity(self.provider, self.claims)
        self.assertEqual(user.email, "person@example.com")
        self.assertEqual((user.first_name, user.last_name), ("Joan", "Camps"))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.has_usable_password())
        self.assertEqual(resolve_microsoft_identity(self.provider, self.claims).pk, user.pk)
        self.assertEqual(ExternalIdentity.objects.filter(provider=self.provider).count(), 1)
        self.assertFalse(ApplicationAssignment.objects.filter(user=user).exists())

    def test_existing_user_is_preserved(self):
        user = get_user_model().objects.create_user("person@example.com", "existing-password", first_name="Existing")
        self.assertEqual(resolve_microsoft_identity(self.provider, self.claims).pk, user.pk)
        user.refresh_from_db()
        self.assertEqual(user.first_name, "Existing")
        self.assertTrue(user.check_password("existing-password"))

    def test_inactive_user_is_not_reactivated(self):
        user = get_user_model().objects.create_user("person@example.com", is_active=False)
        with self.assertRaises(MicrosoftOIDCError):
            resolve_microsoft_identity(self.provider, self.claims)
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertFalse(ExternalIdentity.objects.filter(provider=self.provider).exists())

    def test_disallowed_domain_creates_nothing(self):
        with self.assertRaises(MicrosoftOIDCError):
            resolve_microsoft_identity(self.provider, {**self.claims, "email": "person@other.com"})
        self.assertFalse(get_user_model().objects.filter(email="person@other.com").exists())

    def test_preferred_username_is_supported(self):
        claims = {**self.claims, "email": "", "preferred_username": "person@example.com"}
        self.assertEqual(resolve_microsoft_identity(self.provider, claims).email, "person@example.com")

    def test_linked_inactive_user_is_rejected(self):
        user = resolve_microsoft_identity(self.provider, self.claims)
        user.is_active = False
        user.save()
        with self.assertRaises(MicrosoftOIDCError):
            resolve_microsoft_identity(self.provider, self.claims)
