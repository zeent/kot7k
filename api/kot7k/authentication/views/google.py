from kot7k.authentication.services.sso import begin_session
import secrets
from urllib.parse import urlencode, urlsplit, urlunsplit

from django.core.cache import cache
from django.conf import settings
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from kot7k.authentication.serializers import MeSerializer
from kot7k.authentication.services import (
    GoogleOIDCError,
    build_google_authorization_url,
    exchange_google_code,
    resolve_google_identity,
)
from kot7k.organizations.models import IdentityProvider
from kot7k.authentication.models import AccountActivity
from kot7k.authentication.services.account_activity import record_account_activity


def _provider(request, provider_key):
    return IdentityProvider.objects.filter(
        key=provider_key,
        provider_type=IdentityProvider.Type.GOOGLE,
        is_enabled=True,
    ).first()


def _redirect_uri():
    return (
        f"{settings.EXTERNAL_AUTH_CALLBACK_BASE_URL}"
        "/api/authentication/google/callback/"
    )


def _append_query(url, parameters):
    parts = urlsplit(url)
    query = "&".join(filter(None, (parts.query, urlencode(parameters))))
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, query, parts.fragment)
    )


class GoogleStartView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get(self, request, provider_key):
        provider = _provider(request, provider_key)
        if provider is None:
            return Response({"detail": "Google provider not found."}, status=404)

        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)
        verifier = secrets.token_urlsafe(64)
        cache.set(f"google_oidc:{state}", {
            "provider_id": provider.id,
            "nonce": nonce,
            "verifier": verifier,
        }, timeout=600)
        try:
            authorization_url = build_google_authorization_url(
                provider,
                _redirect_uri(),
                state,
                nonce,
                verifier,
            )
        except GoogleOIDCError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"authorization_url": authorization_url})


class GoogleCallbackView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get(self, request):
        state = request.query_params.get("state", "")
        flow_key = f"google_oidc:{state}"
        flow = cache.get(flow_key)
        cache.delete(flow_key)
        if not flow or request.query_params.get("error"):
            return Response(
                {"detail": "Invalid or cancelled Google login."}, status=400
            )

        provider = IdentityProvider.objects.filter(
            id=flow["provider_id"],
            provider_type=IdentityProvider.Type.GOOGLE,
            is_enabled=True,
        ).first()
        if (
            provider is None
        ):
            return Response(
                {"detail": "Google login context is invalid."}, status=400
            )

        try:
            claims = exchange_google_code(
                provider,
                request.query_params.get("code", ""),
                _redirect_uri(),
                flow["verifier"],
                flow["nonce"],
            )
            user = resolve_google_identity(provider, claims)
        except GoogleOIDCError as exc:
            return Response({"detail": str(exc)}, status=403)

        completion_code = secrets.token_urlsafe(32)
        cache.set(
            f"external_login:{completion_code}",
            {"user_id": user.id, "provider_type": provider.provider_type, "provider_key": provider.key},
            timeout=60,
        )
        frontend_url = provider.configuration.get("frontend_callback_url") or f"{settings.OIDC_FRONTEND_URL}/authentication/login"
        return redirect(
            _append_query(
                frontend_url,
                {"provider": provider.key, "code": completion_code},
            )
        )


class ExternalLoginCompleteView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request):
        completion_code = request.data.get("code", "")
        cache_key = f"external_login:{completion_code}"
        login = cache.get(cache_key)
        cache.delete(cache_key)
        if not login:
            return Response(
                {"detail": "Invalid or expired login code."}, status=400
            )

        from django.contrib.auth import get_user_model
        user = get_user_model().objects.filter(id=login["user_id"], is_active=True).first()
        if user is None:
            return Response(
                {"detail": "Active user account required."},
                status=403,
            )

        refresh = begin_session(request, user, login.get("provider_type", "external"), login.get("provider_key", ""))
        record_account_activity(
            user, AccountActivity.Action.LOGIN, "Signed in to KOT7K.",
            {"method": "external"},
            request=request,
        )
        user_data = MeSerializer(user).data
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": user_data,
            }
        )
