from urllib.parse import parse_qs, urlsplit

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from kot7k.authentication.services.apple_oidc import build_apple_authorization_url
from kot7k.organizations.models import IdentityProvider


class AppleOIDCTests(TestCase):
    def setUp(self):
        self.provider = IdentityProvider.objects.create(
            key="apple",
            provider_type=IdentityProvider.Type.APPLE,
            name="Apple",
            is_enabled=True,
            configuration={
                "client_id": "com.example.kot7k.web",
                "team_id": "TEAM123456",
                "key_id": "KEY1234567",
            },
            secret_reference="env://APPLE_PRIVATE_KEY",
        )

    def test_authorization_request_uses_form_post_and_nonce(self):
        url = build_apple_authorization_url(
            self.provider,
            "https://kot7k.example.com/api/authentication/apple/callback/",
            "state-value",
            "nonce-value",
        )
        query = parse_qs(urlsplit(url).query)
        self.assertEqual(query["response_mode"], ["form_post"])
        self.assertEqual(query["scope"], ["name email"])
        self.assertEqual(query["nonce"], ["nonce-value"])

    @override_settings(EXTERNAL_AUTH_CALLBACK_BASE_URL="https://kot7k.example.com")
    def test_start_endpoint_returns_apple_authorization_url(self):
        response = APIClient().get("/api/authentication/apple/apple/start/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["authorization_url"].startswith(
            "https://appleid.apple.com/auth/authorize?"
        ))
