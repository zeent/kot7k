import secrets
from urllib.parse import urlencode, urlsplit, urlunsplit

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import redirect
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from kot7k.authentication.services.apple_oidc import (
    AppleOIDCError,
    build_apple_authorization_url,
    exchange_apple_code,
    resolve_apple_identity,
)
from kot7k.organizations.models import IdentityProvider


def _redirect_uri():
    return f"{settings.EXTERNAL_AUTH_CALLBACK_BASE_URL}/api/authentication/apple/callback/"


def _append_query(url, parameters):
    parts = urlsplit(url)
    query = "&".join(filter(None, (parts.query, urlencode(parameters))))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))


class AppleStartView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get(self, request, provider_key):
        provider = IdentityProvider.objects.filter(
            key=provider_key,
            provider_type=IdentityProvider.Type.APPLE,
            is_enabled=True,
        ).first()
        if provider is None:
            return Response({"detail": "Apple provider not found."}, status=404)

        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)
        cache.set(
            f"apple_oidc:{state}",
            {"provider_id": provider.id, "nonce": nonce},
            timeout=600,
        )
        try:
            url = build_apple_authorization_url(
                provider, _redirect_uri(), state, nonce
            )
        except AppleOIDCError as exc:
            return Response({"detail": str(exc)}, status=503)
        return Response({"authorization_url": url})


class AppleCallbackView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request):
        state = request.data.get("state", "")
        flow_key = f"apple_oidc:{state}"
        flow = cache.get(flow_key)
        cache.delete(flow_key)
        if not flow or request.data.get("error"):
            return Response({"detail": "Invalid or cancelled Apple login."}, status=400)

        provider = IdentityProvider.objects.filter(
            id=flow["provider_id"],
            provider_type=IdentityProvider.Type.APPLE,
            is_enabled=True,
        ).first()
        if provider is None:
            return Response({"detail": "Apple login context is invalid."}, status=400)

        try:
            claims = exchange_apple_code(
                provider, request.data.get("code", ""), _redirect_uri(), flow["nonce"]
            )
            user = resolve_apple_identity(provider, claims)
        except AppleOIDCError as exc:
            return Response({"detail": str(exc)}, status=403)

        completion_code = secrets.token_urlsafe(32)
        cache.set(f"external_login:{completion_code}", {"user_id": user.id, "provider_type": provider.provider_type, "provider_key": provider.key}, timeout=60)
        frontend_url = provider.configuration.get("frontend_callback_url") or f"{settings.OIDC_FRONTEND_URL}/authentication/login"
        return redirect(_append_query(frontend_url, {
            "provider": provider.key, "code": completion_code
        }))
