import secrets
from urllib.parse import urlencode, urlsplit, urlunsplit

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from kot7k.authentication.services.generic_oidc import GenericOIDCError, build_authorization_url, exchange_code, resolve_identity
from kot7k.organizations.models import IdentityProvider


def _redirect_uri():
    return f"{settings.EXTERNAL_AUTH_CALLBACK_BASE_URL}/api/authentication/oidc/callback/"


def _append_query(url, parameters):
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "&".join(filter(None, (parts.query, urlencode(parameters)))), parts.fragment))


class GenericOIDCStartView(APIView):
    authentication_classes = (); permission_classes = (AllowAny,)

    def get(self, request, provider_key):
        provider = IdentityProvider.objects.filter(key=provider_key, provider_type=IdentityProvider.Type.OIDC, is_enabled=True).first()
        if provider is None:
            return Response({"detail": "OpenID Connect provider not found."}, status=404)
        state, nonce, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(32), secrets.token_urlsafe(64)
        cache.set(f"generic_oidc:{state}", {"provider_id": provider.id, "nonce": nonce, "verifier": verifier}, timeout=600)
        try:
            url = build_authorization_url(provider, _redirect_uri(), state, nonce, verifier)
        except GenericOIDCError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({"authorization_url": url})


class GenericOIDCCallbackView(APIView):
    authentication_classes = (); permission_classes = (AllowAny,)

    def get(self, request):
        state = request.query_params.get("state", "")
        flow = cache.get(f"generic_oidc:{state}"); cache.delete(f"generic_oidc:{state}")
        if not flow or request.query_params.get("error"):
            return Response({"detail": "Invalid or cancelled OpenID Connect login."}, status=400)
        provider = IdentityProvider.objects.filter(id=flow["provider_id"], provider_type=IdentityProvider.Type.OIDC, is_enabled=True).first()
        if provider is None:
            return Response({"detail": "OpenID Connect login context is invalid."}, status=400)
        try:
            claims = exchange_code(provider, request.query_params.get("code", ""), _redirect_uri(), flow["verifier"], flow["nonce"])
            user = resolve_identity(provider, claims)
        except GenericOIDCError as exc:
            return Response({"detail": str(exc)}, status=403)
        completion_code = secrets.token_urlsafe(32)
        cache.set(f"external_login:{completion_code}", {"user_id": user.id, "provider_type": provider.provider_type, "provider_key": provider.key}, timeout=60)
        frontend_url = provider.configuration.get("frontend_callback_url") or f"{settings.OIDC_FRONTEND_URL}/authentication/login"
        return redirect(_append_query(frontend_url, {"provider": provider.key, "code": completion_code}))
