from kot7k.authentication.services.sso import browser_session, active_session
from kot7k.authentication.models import SSOSession
import base64
import re
import secrets
from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views import View
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from kot7k.applications.models import (
    ApplicationAssignment, AuthorizationCode, OAuthClient, OAuthRefreshToken,
)
from kot7k.authentication.services.oidc_provider import (
    OIDCProviderError, decode_access_token, hash_token, issuer, issue_tokens,
    jwks_document, verify_pkce,
)


def _append_query(uri, values):
    return f"{uri}{'&' if '?' in uri else '?'}{urlencode(values)}"


def _oauth_error(error, description, status=400):
    response = JsonResponse({"error": error, "error_description": description}, status=status)
    response["Cache-Control"] = "no-store"
    response["Pragma"] = "no-cache"
    return response


def _authenticate_client(request):
    client_id = request.POST.get("client_id", "")
    client_secret = request.POST.get("client_secret", "")
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Basic "):
        try:
            decoded = base64.b64decode(authorization[6:]).decode()
            client_id, client_secret = decoded.split(":", 1)
        except (ValueError, UnicodeDecodeError):
            return None
    client = OAuthClient.objects.select_related("application").filter(
        client_id=client_id, is_active=True, application__is_active=True
    ).first()
    if client is None:
        return None
    if client.is_confidential and not client.check_secret(client_secret):
        return None
    return client


@method_decorator(never_cache, name="dispatch")
class AuthorizationView(View):
    def get(self, request):
        client_id = request.GET.get("client_id", "")
        redirect_uri = request.GET.get("redirect_uri", "")
        state = request.GET.get("state", "")
        client = OAuthClient.objects.select_related("application").filter(
            client_id=client_id, is_active=True, application__is_active=True
        ).first()
        if client is None or redirect_uri not in client.redirect_uris:
            return _oauth_error("invalid_request", "Unknown client or redirect URI.")

        def redirect_error(error, description):
            values = {"error": error, "error_description": description}
            if state:
                values["state"] = state
            return redirect(_append_query(redirect_uri, values))

        if request.GET.get("response_type") != "code":
            return redirect_error("unsupported_response_type", "Only response_type=code is supported.")
        scopes = request.GET.get("scope", "").split()
        if "openid" not in scopes or not set(scopes).issubset(set(client.allowed_scopes)):
            return redirect_error("invalid_scope", "The requested scopes are not allowed.")
        nonce = request.GET.get("nonce", "")
        challenge = request.GET.get("code_challenge", "")
        if not state or not nonce:
            return redirect_error("invalid_request", "state and nonce are required.")
        if (
            request.GET.get("code_challenge_method") != "S256"
            or not re.fullmatch(r"[A-Za-z0-9_-]{43}", challenge)
        ):
            return redirect_error("invalid_request", "PKCE with S256 is required.")

        if not request.user.is_authenticated:
            login_url = f"{settings.OIDC_FRONTEND_URL}/authentication/login"
            return redirect(_append_query(login_url, {"next": request.build_absolute_uri()}))
        if not request.user.is_active:
            return redirect_error("access_denied", "The user account is inactive.")
        if not ApplicationAssignment.objects.filter(
            application=client.application, user=request.user
        ).exists():
            return redirect_error("access_denied", "The user has no access to this application.")

        session = browser_session(request)
        if session is None:
            return redirect_error("login_required", "The session has ended.")
        raw_code = secrets.token_urlsafe(48)
        AuthorizationCode.objects.create(
            session=session,
            code_hash=hash_token(raw_code),
            client=client,
            user=request.user,
            redirect_uri=redirect_uri,
            scopes=scopes,
            nonce=nonce,
            code_challenge=challenge,
            expires_at=timezone.now() + timedelta(seconds=settings.OIDC_AUTHORIZATION_CODE_LIFETIME),
        )
        return redirect(_append_query(redirect_uri, {"code": raw_code, "state": state}))


class TokenView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request):
        client = _authenticate_client(request._request)
        if client is None:
            response = _oauth_error("invalid_client", "Client authentication failed.", 401)
            response["WWW-Authenticate"] = 'Basic realm="token"'
            return response

        grant_type = request.data.get("grant_type", "")
        if grant_type == "authorization_code":
            return self._authorization_code(request, client)
        if grant_type == "refresh_token":
            return self._refresh_token(request, client)
        return _oauth_error("unsupported_grant_type", "Unsupported grant type.")

    @transaction.atomic
    def _authorization_code(self, request, client):
        sid = AuthorizationCode.objects.filter(code_hash=hash_token(request.data.get("code", "")), client=client).values_list("session_id", flat=True).first()
        SSOSession.objects.select_for_update().filter(pk=sid).first()
        code = AuthorizationCode.objects.select_for_update().select_related("user").filter(
            code_hash=hash_token(request.data.get("code", "")), client=client
        ).first()
        now = timezone.now()
        if code is None or not code.user.is_active or code.used_at or code.expires_at <= now or not active_session(code.session_id, code.user_id):
            return _oauth_error("invalid_grant", "Invalid or expired authorization code.")
        if code.redirect_uri != request.data.get("redirect_uri", ""):
            return _oauth_error("invalid_grant", "The redirect URI does not match.")
        if not verify_pkce(request.data.get("code_verifier", ""), code.code_challenge):
            return _oauth_error("invalid_grant", "PKCE verification failed.")
        code.used_at = now
        code.save(update_fields=("used_at",))
        return Response(issue_tokens(
            code.user, client, code.scopes, nonce=code.nonce,
            include_refresh="offline_access" in code.scopes, session=code.session,
        ), headers={"Cache-Control": "no-store", "Pragma": "no-cache"})

    @transaction.atomic
    def _refresh_token(self, request, client):
        sid = OAuthRefreshToken.objects.filter(token_hash=hash_token(request.data.get("refresh_token", "")), client=client).values_list("session_id", flat=True).first()
        SSOSession.objects.select_for_update().filter(pk=sid).first()
        token = OAuthRefreshToken.objects.select_for_update().select_related("user").filter(
            token_hash=hash_token(request.data.get("refresh_token", "")), client=client
        ).first()
        now = timezone.now()
        if token is None or token.revoked_at or token.expires_at <= now or not token.user.is_active or not active_session(token.session_id, token.user_id):
            return _oauth_error("invalid_grant", "Invalid or expired refresh token.")
        if not ApplicationAssignment.objects.filter(
            application=client.application, user=token.user
        ).exists():
            return _oauth_error("invalid_grant", "The user no longer has access to this application.")
        token.revoked_at = now
        token.save(update_fields=("revoked_at",))
        return Response(issue_tokens(token.user, client, token.scopes, include_refresh=True, session=token.session), headers={
            "Cache-Control": "no-store", "Pragma": "no-cache",
        })


class UserInfoView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get(self, request):
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return _oauth_error("invalid_token", "A bearer token is required.", 401)
        try:
            claims = decode_access_token(authorization[7:])
        except OIDCProviderError as exc:
            return _oauth_error("invalid_token", str(exc), 401)
        if claims.get("token_use") != "access":
            return _oauth_error("invalid_token", "An access token is required.", 401)
        user = get_user_model().objects.filter(
            oidc_subject=claims.get("sub"), is_active=True
        ).first()
        if user is None:
            return _oauth_error("invalid_token", "The user no longer exists.", 401)
        return Response({
            "sub": str(user.oidc_subject), "email": user.email, "email_verified": True,
            "name": user.get_full_name(), "given_name": user.first_name,
            "family_name": user.last_name, "roles": claims.get("roles", []),
        })


class RevocationView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request):
        client = _authenticate_client(request._request)
        if client is not None:
            OAuthRefreshToken.objects.filter(
                token_hash=hash_token(request.data.get("token", "")), client=client,
                revoked_at__isnull=True,
            ).update(revoked_at=timezone.now())
        return Response(status=200)


def discovery(request):
    base = issuer()
    return JsonResponse({
        "issuer": base,
        "authorization_endpoint": f"{base}/oauth/authorize/",
        "token_endpoint": f"{base}/oauth/token/",
        "userinfo_endpoint": f"{base}/oauth/userinfo/",
        "jwks_uri": f"{base}/.well-known/jwks.json",
        "end_session_endpoint": f"{base}/oauth/logout/",
        "backchannel_logout_supported": True,
        "backchannel_logout_session_supported": True,
        "revocation_endpoint": f"{base}/oauth/revoke/",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "scopes_supported": ["openid", "profile", "email", "roles", "offline_access"],
        "claims_supported": ["sid", "sub", "iss", "aud", "exp", "iat", "nonce", "name", "given_name", "family_name", "email", "email_verified", "roles"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post", "none"],
    })


def jwks(request):
    try:
        return JsonResponse(jwks_document())
    except OIDCProviderError as exc:
        return JsonResponse({"detail": str(exc)}, status=503)
