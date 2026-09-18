import secrets
from urllib.parse import urlencode

import jwt
from django.conf import settings
from django.contrib.auth import logout
from django.core import signing
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import redirect
from django.utils.html import format_html
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import TokenError

from kot7k.applications.models import OAuthClient
from kot7k.authentication.services.oidc_provider import _public_key_object, issuer, OIDCProviderError
from kot7k.authentication.services.sso import browser_session, revoke_session
from kot7k.authentication.models import AccountActivity
from kot7k.authentication.services.account_activity import record_account_activity


@method_decorator([csrf_protect, never_cache], name="dispatch")
class EndSessionView(View):
    def get(self, request):
        client_id = request.GET.get("client_id", "")
        hint = request.GET.get("id_token_hint", "")
        claims = None
        if hint:
            try:
                # An expired but correctly signed ID token is a valid logout hint.
                claims = jwt.decode(hint, _public_key_object(), algorithms=["RS256"], issuer=issuer(), options={"verify_exp": False, "verify_aud": False}, leeway=10)
                if claims.get("token_use") != "id" or not claims.get("sid"):
                    raise ValueError("ID token required")
                if client_id and claims.get("aud") != client_id:
                    raise ValueError("Client mismatch")
                client_id = claims["aud"]
                if not isinstance(client_id, str):
                    raise ValueError("Client required")
            except (jwt.PyJWTError, ValueError, TypeError, KeyError, OIDCProviderError):
                return JsonResponse({"error": "invalid_request"}, status=400)
        client = OAuthClient.objects.filter(client_id=client_id, is_active=True).first() if client_id else None
        target = request.GET.get("post_logout_redirect_uri", "")
        if (client_id and client is None) or (target and (client is None or target not in client.post_logout_redirect_uris)):
            return JsonResponse({"error": "invalid_request", "detail": "Unregistered logout redirect."}, status=400)
        if not request.user.is_authenticated:
            return HttpResponse("<p>No active KOT7K session.</p>", content_type="text/html")
        session = browser_session(request)
        if session is None or (claims and (claims["sid"] != str(session.pk) or claims.get("sub") != str(request.user.oidc_subject))):
            return JsonResponse({"error": "invalid_request", "detail": "Session mismatch."}, status=400)
        if target and request.GET.get("state"):
            target += ("&" if "?" in target else "?") + urlencode({"state": request.GET["state"]})
        key = secrets.token_urlsafe(32)
        cache.set(f"logout_request:{key}", {"sid": str(session.pk), "target": target}, 300)
        response = HttpResponse(format_html(
            '<!doctype html><html lang="ca"><title>KOT7K</title><h1>Tancar la sessió?</h1><p>Sortiràs de KOT7K i de les aplicacions vinculades a aquesta sessió. Microsoft continuarà obert.</p><form method="post"><input type="hidden" name="csrfmiddlewaretoken" value="{}"><input type="hidden" name="request" value="{}"><button type="submit">Tanca la sessió</button></form></html>',
            get_token(request), key,
        ))
        response["Referrer-Policy"] = "no-referrer"
        response["Content-Security-Policy"] = "default-src 'none'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
        return response

    def post(self, request):
        key = request.POST.get("request", "")
        flow = cache.get(f"logout_request:{key}")
        if not flow or flow["sid"] != request.session.get("sso_sid") or not request.user.is_authenticated:
            return JsonResponse({"error": "invalid_request"}, status=400)
        cache.delete(f"logout_request:{key}")
        session = revoke_session(flow["sid"])
        if session:
            record_account_activity(session.user, AccountActivity.Action.LOGOUT, "Signed out of the KOT7K ecosystem.", {"sid": flow["sid"]}, request=request)
        logout(request)
        ticket = signing.dumps(flow, salt="sso-logout-complete")
        return redirect(f'{settings.OIDC_FRONTEND_URL}/authentication/signed-out?{urlencode({"ticket": ticket})}')


class LogoutCompleteView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            flow = signing.loads(request.data.get("ticket", ""), salt="sso-logout-complete", max_age=300)
        except (signing.BadSignature, TypeError):
            return Response({"detail": "Invalid logout confirmation."}, status=400)
        matches = False
        if request.data.get("refresh"):
            try:
                claims = UntypedToken(request.data["refresh"])
                matches = claims.get("token_type") == "refresh" and claims.get("sid") == flow["sid"]
            except TokenError:
                pass
        return Response({"clear_session": matches, "redirect_uri": flow["target"]}, headers={"Cache-Control": "no-store"})
