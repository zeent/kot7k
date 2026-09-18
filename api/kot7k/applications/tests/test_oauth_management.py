from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from kot7k.applications.models import Application, OAuthClient


class OAuthManagementTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser('admin@example.com', 'password')
        self.user = get_user_model().objects.create_user('user@example.com', 'password')
        self.application = Application.objects.create(name='Talaia', key='talaia')
        self.url = f'/api/applications/{self.application.pk}/oidc/'
        self.client = APIClient()
        self.client.force_authenticate(self.admin)
        self.payload = {'is_confidential': True, 'redirect_uris': ['http://localhost:8000/api/authentication/oidc/callback/'], 'allowed_scopes': ['openid', 'email', 'profile'], 'is_active': True}

    def test_create_update_and_rotate_secret(self):
        self.assertIsNone(self.client.get(self.url).data)
        response = self.client.put(self.url, self.payload, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response['Cache-Control'], 'no-store')
        secret = response.data['client_secret']
        client_id = response.data['client_id']
        model = OAuthClient.objects.get(application=self.application)
        self.assertTrue(model.check_secret(secret))
        self.assertNotEqual(model.client_secret_hash, secret)
        self.assertNotIn('client_secret', self.client.get(self.url).data)
        self.assertNotIn('client_secret_hash', self.client.get(self.url).data)
        response = self.client.put(self.url, {**self.payload, 'is_active': False}, format='json')
        self.assertNotIn('client_secret', response.data)
        self.assertEqual(response.data['client_id'], client_id)
        model.refresh_from_db()
        self.assertTrue(model.check_secret(secret))
        self.assertFalse(model.is_active)
        response = self.client.post(self.url + 'rotate-secret/')
        model.refresh_from_db()
        self.assertFalse(model.check_secret(secret))
        self.assertTrue(model.check_secret(response.data['client_secret']))
        self.assertEqual(model.client_id, client_id)

    def test_public_client_and_conversion(self):
        response = self.client.put(self.url, {**self.payload, 'is_confidential': False}, format='json')
        self.assertNotIn('client_secret', response.data)
        self.assertEqual(self.client.post(self.url + 'rotate-secret/').status_code, 400)
        response = self.client.put(self.url, self.payload, format='json')
        self.assertIn('client_secret', response.data)
        self.client.put(self.url, {**self.payload, 'is_confidential': False}, format='json')
        self.assertEqual(OAuthClient.objects.get(application=self.application).client_secret_hash, '')

    def test_invalid_redirects_and_scopes_do_not_create_client(self):
        for uri in ['https://example.com/#fragment', 'https://*.example.com/callback', 'javascript:alert(1)', 'http://example.com/callback', '/callback', 'https://user:password@example.com', 'https://example.com:invalid/callback']:
            response = self.client.put(self.url, {**self.payload, 'redirect_uris': [uri]}, format='json')
            self.assertEqual(response.status_code, 400, uri)
        for values in ([], ['email'], ['openid', 'unknown']):
            self.assertEqual(self.client.put(self.url, {**self.payload, 'allowed_scopes': values}, format='json').status_code, 400)
        self.assertFalse(OAuthClient.objects.exists())

    def test_permission_checks_for_all_operations(self):
        for user, expected in ((self.user, 403), (None, 401)):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(self.url).status_code, expected)
            self.assertEqual(self.client.put(self.url, self.payload, format='json').status_code, expected)
            self.assertEqual(self.client.post(self.url + 'rotate-secret/').status_code, expected)

    def test_existing_logout_configuration_is_preserved(self):
        self.client.put(self.url, self.payload, format='json')
        OAuthClient.objects.filter(application=self.application).update(backchannel_logout_uri='https://talaia.example.com/logout', post_logout_redirect_uris=['https://talaia.example.com/'])
        self.client.put(self.url, self.payload, format='json')
        client = OAuthClient.objects.get(application=self.application)
        self.assertEqual(client.backchannel_logout_uri, 'https://talaia.example.com/logout')
        self.assertEqual(client.post_logout_redirect_uris, ['https://talaia.example.com/'])
