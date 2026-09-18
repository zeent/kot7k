from importlib import import_module
from types import SimpleNamespace

from django.apps import apps
from django.db import connection
from django.test import TestCase
from django.urls import Resolver404, resolve

from kot7k.applications.models import Application, ApplicationAssignment, ApplicationRole
from django.contrib.auth import get_user_model


class IAMScopeTests(TestCase):
    def test_removed_api_routes_do_not_resolve(self):
        for path in ["/api/assets/", "/api/support/", "/api/support/summary/"]:
            with self.subTest(path=path), self.assertRaises(Resolver404):
                resolve(path)

    def test_iam_routes_remain_available(self):
        for path in ["/api/dashboard/", "/api/authentication/login/", "/api/applications/", "/.well-known/openid-configuration"]:
            with self.subTest(path=path):
                self.assertIsNotNone(resolve(path).func)

    def test_retirement_preserves_assignments_and_external_apps(self):
        internal = Application.objects.create(key="kot7k-support", name="Support", homepage_url="/support")
        external = Application.objects.create(key="talaia-support", name="External support", homepage_url="https://support.example.com")
        user = get_user_model().objects.create_user("scope@example.com")
        role = ApplicationRole.objects.create(application=internal, key="reader", name="Reader")
        assignment = ApplicationAssignment.objects.create(application=internal, user=user, role=role)
        retire = import_module("kot7k.applications.migrations.0004_retire_internal_support").retire_internal_support
        for _ in range(2):
            retire(apps, SimpleNamespace(connection=connection))
        internal.refresh_from_db()
        external.refresh_from_db()
        self.assertFalse(internal.is_active)
        self.assertTrue(external.is_active)
        self.assertTrue(ApplicationAssignment.objects.filter(pk=assignment.pk).exists())
