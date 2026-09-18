import base64
import hashlib
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import TestCase, override_settings

from kot7k.applications.models import Application, ApplicationAssignment, ApplicationRole, OAuthClient
from kot7k.authentication.models import User


@override_settings(
    OIDC_ISSUER="https://kot7k.example",
    OIDC_FRONTEND_URL="http://localhost:10000",
    OIDC_PRIVATE_KEY_ENV="TEST_OIDC_PRIVATE_KEY",
    OIDC_PUBLIC_KEY_ENV="TEST_OIDC_PUBLIC_KEY",
    OIDC_KEY_ID="test-key",
)
class OIDCProviderTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.private_pem = key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode()
        cls.public_pem = key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()
        cls.key_environment = patch.dict("os.environ", {
            "TEST_OIDC_PRIVATE_KEY": cls.private_pem,
            "TEST_OIDC_PUBLIC_KEY": cls.public_pem,
        })
        cls.key_environment.start()

    @classmethod
    def tearDownClass(cls):
        cls.key_environment.stop()
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(
            "joan@example.com", "secret", first_name="Joan", last_name="Camps"
        )
        self.application = Application.objects.create(key="dash", name="Dash")
        self.role = ApplicationRole.objects.create(
            application=self.application, key="administrator", name="Administrator"
        )
        ApplicationAssignment.objects.create(
            application=self.application, role=self.role, user=self.user
        )
        self.oauth_client = OAuthClient.objects.create(
            application=self.application,
            client_id="dash-client",
            is_confidential=False,
            redirect_uris=["http://localhost:3000/auth/callback"],
        )
        self.verifier = "a" * 64
        self.challenge = base64.urlsafe_b64encode(
            hashlib.sha256(self.verifier.encode()).digest()
        ).rstrip(b"=").decode()

    def authorization_params(self, **overrides):
        values = {
            "client_id": self.oauth_client.client_id,
            "redirect_uri": self.oauth_client.redirect_uris[0],
            "response_type": "code",
            "scope": "openid profile email roles offline_access",
            "state": "expected-state",
            "nonce": "expected-nonce",
            "code_challenge": self.challenge,
            "code_challenge_method": "S256",
        }
        values.update(overrides)
        return values

    def authorize(self):
        self.client.force_login(self.user)
        response = self.client.get("/oauth/authorize/", self.authorization_params())
        self.assertEqual(response.status_code, 302)
        query = parse_qs(urlparse(response["Location"]).query)
        self.assertEqual(query["state"], ["expected-state"])
        return query["code"][0]

    def test_discovery_and_jwks_publish_pkce_and_rsa_key(self):
        discovery = self.client.get("/.well-known/openid-configuration").json()
        self.assertEqual(discovery["issuer"], "https://kot7k.example")
        self.assertEqual(discovery["code_challenge_methods_supported"], ["S256"])
        self.assertEqual(discovery["response_types_supported"], ["code"])
        key = self.client.get("/.well-known/jwks.json").json()["keys"][0]
        self.assertEqual(key["kid"], "test-key")
        self.assertEqual(key["alg"], "RS256")

    def test_anonymous_user_is_sent_to_kot7k_login(self):
        response = self.client.get("/oauth/authorize/", self.authorization_params())
        self.assertEqual(response.status_code, 302)
        target = urlparse(response["Location"])
        self.assertEqual(target.path, "/authentication/login")
        self.assertIn("/oauth/authorize/", parse_qs(target.query)["next"][0])

    def test_code_pkce_tokens_userinfo_refresh_rotation_and_code_reuse(self):
        code = self.authorize()
        payload = {
            "grant_type": "authorization_code",
            "client_id": "dash-client",
            "code": code,
            "redirect_uri": self.oauth_client.redirect_uris[0],
            "code_verifier": self.verifier,
        }
        response = self.client.post("/oauth/token/", payload)
        self.assertEqual(response.status_code, 200, response.content)
        tokens = response.json()
        claims = jwt.decode(
            tokens["id_token"], self.public_pem, algorithms=["RS256"],
            audience="dash-client", issuer="https://kot7k.example",
        )
        self.assertEqual(claims["sub"], str(self.user.oidc_subject))
        self.assertEqual(claims["nonce"], "expected-nonce")
        self.assertEqual(claims["roles"], ["administrator"])
        self.assertEqual(claims["email"], "joan@example.com")

        userinfo = self.client.get(
            "/oauth/userinfo/", HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}"
        )
        self.assertEqual(userinfo.status_code, 200)
        self.assertEqual(userinfo.json()["roles"], ["administrator"])

        reused = self.client.post("/oauth/token/", payload)
        self.assertEqual(reused.status_code, 400)
        self.assertEqual(reused.json()["error"], "invalid_grant")

        refreshed = self.client.post("/oauth/token/", {
            "grant_type": "refresh_token", "client_id": "dash-client",
            "refresh_token": tokens["refresh_token"],
        })
        self.assertEqual(refreshed.status_code, 200)
        self.assertNotEqual(refreshed.json()["refresh_token"], tokens["refresh_token"])

    def test_wrong_pkce_verifier_is_rejected(self):
        code = self.authorize()
        response = self.client.post("/oauth/token/", {
            "grant_type": "authorization_code", "client_id": "dash-client",
            "code": code, "redirect_uri": self.oauth_client.redirect_uris[0],
            "code_verifier": "wrong-verifier",
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "invalid_grant")

    def test_user_without_assignment_is_denied(self):
        outsider = User.objects.create_user("outside@example.com", "secret")
        self.client.force_login(outsider)
        response = self.client.get("/oauth/authorize/", self.authorization_params())
        query = parse_qs(urlparse(response["Location"]).query)
        self.assertEqual(query["error"], ["access_denied"])
        self.assertEqual(query["state"], ["expected-state"])

    def login_tokens(self, browser=None):
        response = (browser or self.client).post('/api/authentication/login/', {'email': self.user.email, 'password': 'secret'})
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def app_tokens(self, browser=None):
        browser = browser or self.client
        response = browser.get('/oauth/authorize/', self.authorization_params())
        code = parse_qs(urlparse(response['Location']).query)['code'][0]
        response = browser.post('/oauth/token/', {'grant_type': 'authorization_code', 'client_id': 'dash-client', 'code': code, 'redirect_uri': self.oauth_client.redirect_uris[0], 'code_verifier': self.verifier})
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def test_central_logout_revokes_tokens_but_preserves_other_browser(self):
        from django.test import Client
        first = self.login_tokens()
        app = self.app_tokens()
        other = Client()
        second = self.login_tokens(other)
        other_app = self.app_tokens(other)
        self.oauth_client.backchannel_logout_uri = 'https://dash.example/logout/backchannel'
        self.oauth_client.save()
        with patch('kot7k.authentication.services.sso.requests.post') as post:
            post.return_value.status_code = 200
            with self.captureOnCommitCallbacks(execute=True):
                self.assertEqual(self.client.post('/api/authentication/logout/', {'refresh': first['refresh']}).status_code, 204)
            self.assertEqual(post.call_count, 1)
            claims = jwt.decode(post.call_args.kwargs['data']['logout_token'], self.public_pem, algorithms=['RS256'], audience='dash-client', issuer='https://kot7k.example')
            self.assertEqual(claims['sid'], jwt.decode(app['id_token'], options={'verify_signature': False})['sid'])
            self.assertEqual(claims['events'], {'http://schemas.openid.net/event/backchannel-logout': {}})
            self.assertNotIn('nonce', claims)
        self.assertEqual(self.client.get('/api/authentication/me/', HTTP_AUTHORIZATION=f"Bearer {first['access']}").status_code, 401)
        self.assertEqual(self.client.post('/api/authentication/refresh/', {'refresh': first['refresh']}).status_code, 401)
        self.assertEqual(self.client.get('/oauth/userinfo/', HTTP_AUTHORIZATION=f"Bearer {app['access_token']}").status_code, 401)
        self.assertEqual(self.client.post('/oauth/token/', {'grant_type': 'refresh_token', 'client_id': 'dash-client', 'refresh_token': app['refresh_token']}).status_code, 400)
        self.assertEqual(other.get('/api/authentication/me/', HTTP_AUTHORIZATION=f"Bearer {second['access']}").status_code, 200)
        self.assertEqual(other.get('/oauth/userinfo/', HTTP_AUTHORIZATION=f"Bearer {other_app['access_token']}").status_code, 200)

    def test_microsoft_logout_preserves_local_session(self):
        from kot7k.authentication.models import SSOSession
        tokens = self.login_tokens()
        response = self.client.post('/api/authentication/microsoft/logout/', {'refresh': tokens['refresh']})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['logged_out'])
        self.assertIsNone(SSOSession.objects.get().revoked_at)
        SSOSession.objects.update(provider_type='microsoft')
        self.assertEqual(self.client.post('/api/authentication/microsoft/logout/', {'refresh': tokens['refresh']}).status_code, 204)
        self.assertIsNotNone(SSOSession.objects.get().revoked_at)

    def test_failed_notification_is_retried(self):
        from kot7k.authentication.models import SSOSession, LogoutDelivery
        from kot7k.authentication.services.sso import deliver_pending
        tokens = self.login_tokens()
        self.app_tokens()
        self.oauth_client.backchannel_logout_uri = 'https://dash.example/logout/backchannel'
        self.oauth_client.save()
        with patch('kot7k.authentication.services.sso.requests.post') as post:
            post.return_value.status_code = 503
            with self.captureOnCommitCallbacks(execute=True):
                self.client.post('/api/authentication/logout/', {'refresh': tokens['refresh']})
            self.assertIsNotNone(SSOSession.objects.get().revoked_at)
            self.assertIsNone(LogoutDelivery.objects.get().delivered_at)
            post.return_value.status_code = 200
            self.assertEqual(deliver_pending(), 1)
            self.assertEqual(deliver_pending(), 0)
            self.assertEqual(LogoutDelivery.objects.get().attempts, 2)

    def test_rp_logout_confirmation_csrf_and_redirect_validation(self):
        import re
        from django.test import Client
        from kot7k.authentication.models import SSOSession
        self.client = Client(enforce_csrf_checks=True)
        tokens = self.login_tokens()
        app = self.app_tokens()
        self.oauth_client.post_logout_redirect_uris = ['https://dash.example/signed-out']
        self.oauth_client.save()
        params = {'id_token_hint': app['id_token'], 'post_logout_redirect_uri': 'https://evil.example/'}
        self.assertEqual(self.client.get('/oauth/logout/', params).status_code, 400)
        params.update(post_logout_redirect_uri='https://dash.example/signed-out', state='round trip')
        response = self.client.get('/oauth/logout/', params)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(SSOSession.objects.get().revoked_at)
        key = re.search('name="request" value="([^"]+)"', response.content.decode())[1]
        self.assertEqual(self.client.post('/oauth/logout/', {'request': key}).status_code, 403)
        response = self.client.post('/oauth/logout/', {'request': key, 'csrfmiddlewaretoken': self.client.cookies['csrftoken'].value})
        self.assertEqual(response.status_code, 302)
        self.assertIsNotNone(SSOSession.objects.get().revoked_at)
        ticket = parse_qs(urlparse(response['Location']).query)['ticket'][0]
        complete = self.client.post('/api/authentication/logout/complete/', {'ticket': ticket, 'refresh': tokens['refresh']})
        self.assertTrue(complete.json()['clear_session'])
        self.assertEqual(complete.json()['redirect_uri'], 'https://dash.example/signed-out?state=round+trip')
        new_tokens = self.login_tokens()
        complete = self.client.post('/api/authentication/logout/complete/', {'ticket': ticket, 'refresh': new_tokens['refresh']})
        self.assertFalse(complete.json()['clear_session'])
        self.assertEqual(self.client.post('/api/authentication/logout/complete/', {'ticket': ticket + 'tampered'}).status_code, 400)

    def test_relogin_replaces_session_and_logout_notifies_every_participating_app(self):
        from kot7k.authentication.models import SSOSession, SessionApplication
        first = self.login_tokens()
        second = self.login_tokens()
        self.assertEqual(SSOSession.objects.filter(revoked_at__isnull=True).count(), 1)
        self.assertEqual(self.client.get('/api/authentication/me/', HTTP_AUTHORIZATION=f"Bearer {first['access']}").status_code, 401)
        self.app_tokens()
        app2 = Application.objects.create(key='lynkr', name='Lynkr')
        client2 = OAuthClient.objects.create(application=app2, client_id='lynkr-client', backchannel_logout_uri='https://lynkr.example/logout')
        SessionApplication.objects.create(session=SSOSession.objects.get(revoked_at__isnull=True), client=client2)
        self.oauth_client.backchannel_logout_uri = 'https://dash.example/logout'
        self.oauth_client.save()
        with patch('kot7k.authentication.services.sso.requests.post') as post:
            post.return_value.status_code = 200
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post('/api/authentication/logout/', {'refresh': second['refresh']})
            self.assertEqual(response.status_code, 204)
            self.assertEqual({call.args[0] for call in post.call_args_list}, {'https://dash.example/logout', 'https://lynkr.example/logout'})

    def test_unused_authorization_code_is_revoked_on_logout(self):
        tokens = self.login_tokens()
        response = self.client.get('/oauth/authorize/', self.authorization_params())
        code = parse_qs(urlparse(response['Location']).query)['code'][0]
        self.client.post('/api/authentication/logout/', {'refresh': tokens['refresh']})
        response = self.client.post('/oauth/token/', {'grant_type': 'authorization_code', 'client_id': 'dash-client', 'code': code, 'redirect_uri': self.oauth_client.redirect_uris[0], 'code_verifier': self.verifier})
        self.assertEqual(response.status_code, 400)
