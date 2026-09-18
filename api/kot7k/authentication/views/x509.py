import secrets
from urllib.parse import urlencode, urlsplit, urlunsplit

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import redirect
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from kot7k.authentication.services.x509 import (
    X509AuthenticationError,
    load_verified_client_certificate,
    resolve_x509_identity,
)
from kot7k.organizations.models import IdentityProvider


def _callback_url(state):
    return (
        f"{settings.EXTERNAL_AUTH_CALLBACK_BASE_URL}"
        f"/api/authentication/x509/callback/?{urlencode({'state': state})}"
    )


def _append_query(url, parameters):
    parts = urlsplit(url)
    query = "&".join(filter(None, (parts.query, urlencode(parameters))))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))


class X509StartView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get(self, request, provider_key):
        provider = IdentityProvider.objects.filter(
            key=provider_key,
            provider_type=IdentityProvider.Type.X509,
            is_enabled=True,
        ).first()
        if provider is None:
            return Response({"detail": "Certificate provider not found."}, status=404)
        state = secrets.token_urlsafe(32)
        cache.set(
            f"x509_login:{state}",
            {"provider_id": provider.id},
            timeout=600,
        )
        return Response({"authentication_url": _callback_url(state)})


class X509CallbackView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get(self, request):
        state = request.query_params.get("state", "")
        key = f"x509_login:{state}"
        flow = cache.get(key)
        cache.delete(key)
        if not flow:
            return Response({"detail": "Invalid or expired certificate login."}, status=400)
        provider = IdentityProvider.objects.filter(
            id=flow["provider_id"],
            provider_type=IdentityProvider.Type.X509,
            is_enabled=True,
        ).first()
        if provider is None:
            return Response({"detail": "Certificate login context is invalid."}, status=400)

        request.x509_trusted_proxy_ips = settings.X509_TRUSTED_PROXY_IPS
        try:
            certificate = load_verified_client_certificate(request)
            user = resolve_x509_identity(provider, certificate)
        except X509AuthenticationError as exc:
            return Response({"detail": str(exc)}, status=403)

        completion_code = secrets.token_urlsafe(32)
        cache.set(
            f"external_login:{completion_code}",
            {"user_id": user.id, "provider_type": provider.provider_type, "provider_key": provider.key},
            timeout=60,
        )
        frontend_url = provider.configuration.get("frontend_callback_url")
        if frontend_url:
            return redirect(
                _append_query(frontend_url, {"provider": provider.key, "code": completion_code})
            )
        return Response({"code": completion_code})
