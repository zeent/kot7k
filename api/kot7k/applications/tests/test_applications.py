from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from rest_framework.test import APIClient

from kot7k.applications.models import Application, ApplicationAssignment, ApplicationRole
from kot7k.authentication.models import AccountActivity
from kot7k.organizations.models import IdentityProvider


class ApplicationDirectoryTests(TestCase):
    def test_assignment_links_user_directly_to_application_role(self):
        user = get_user_model().objects.create_user("person@example.com")
        application = Application.objects.create(key="lynkr", name="Lynkr")
        role = ApplicationRole.objects.create(application=application, key="admin", name="Admin")
        assignment = ApplicationAssignment.objects.create(application=application, user=user, role=role)
        self.assertEqual(assignment.user, user)

    def test_application_key_is_global(self):
        Application.objects.create(key="lynkr", name="Lynkr")
        with self.assertRaises(IntegrityError):
            Application.objects.create(key="lynkr", name="Another Lynkr")

    def test_dashboard_contains_metrics_only_assigned_apps_and_account_activity(self):
        existing_applications = Application.objects.filter(is_active=True).count()
        User = get_user_model()
        user = User.objects.create_user("person@example.com")
        User.objects.create_user("other@example.com")
        assigned = Application.objects.create(
            key="lynkr", name="Lynkr", homepage_url="https://lynkr.example.com"
        )
        Application.objects.create(key="private", name="Private")
        role = ApplicationRole.objects.create(application=assigned, key="reader", name="Reader")
        ApplicationAssignment.objects.create(application=assigned, user=user, role=role)
        IdentityProvider.objects.create(
            key="local", provider_type=IdentityProvider.Type.LOCAL,
            name="Local", is_enabled=True,
        )

        client = APIClient()
        client.force_authenticate(user)
        response = client.get("/api/dashboard/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["metrics"], {
            "users": 2, "applications": existing_applications + 3, "identity_providers": 2,
        })
        self.assertEqual(len(response.json()["applications"]), 1)
        self.assertEqual(response.json()["applications"][0]["key"], "lynkr")
        self.assertEqual(response.json()["applications"][0]["roles"], [
            {"key": "reader", "name": "Reader"}
        ])
        self.assertEqual(response.json()["activities"][0]["action"], "role_assigned")

    def test_assignment_removal_is_recorded_for_the_user(self):
        user = get_user_model().objects.create_user("person@example.com")
        application = Application.objects.create(key="lynkr", name="Lynkr")
        role = ApplicationRole.objects.create(application=application, key="reader", name="Reader")
        assignment = ApplicationAssignment.objects.create(
            application=application, user=user, role=role
        )
        assignment.delete()
        self.assertTrue(AccountActivity.objects.filter(
            user=user, action=AccountActivity.Action.ROLE_REMOVED
        ).exists())

    def test_dashboard_requires_authentication(self):
        response = APIClient().get("/api/dashboard/")
        self.assertEqual(response.status_code, 401)

    def test_kot7k_administration_app_is_only_visible_to_superusers(self):
        regular = get_user_model().objects.create_user("person@example.com")
        administrator = get_user_model().objects.create_superuser("admin@example.com", "secret")
        client = APIClient()

        client.force_authenticate(regular)
        regular_apps = client.get("/api/dashboard/").json()["applications"]
        self.assertNotIn("kot7k-administration", [app["key"] for app in regular_apps])

        client.force_authenticate(administrator)
        administrator_apps = client.get("/api/dashboard/").json()["applications"]
        administration = next(
            app for app in administrator_apps if app["key"] == "kot7k-administration"
        )
        self.assertEqual(administration["homepage_url"], "/administration")

        unassigned = Application.objects.create(key="unassigned", name="Unassigned")
        administrator_apps = client.get("/api/dashboard/").json()["applications"]
        self.assertIn(unassigned.key, [app["key"] for app in administrator_apps])
