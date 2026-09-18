from django.contrib.auth import logout as session_logout
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken
from kot7k.authentication.models import AccountActivity, SSOSession
from kot7k.authentication.services.account_activity import record_account_activity
from kot7k.authentication.services.sso import revoke_session


class LogoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    microsoft_only = False

    def post(self, request):
        raw = request.data.get("refresh")
        if not raw:
            return Response({"detail": "Missing refresh token"}, status=400)
        try:
            # Verify signature and expiry; allow idempotent logout of a token
            # that has already been blacklisted in this session.
            claims = UntypedToken(raw)
            if claims.get("token_type") != "refresh":
                raise TokenError("Refresh token required")
        except TokenError:
            return Response({"detail": "Invalid refresh token"}, status=400)
        session = SSOSession.objects.filter(pk=claims.get("sid"), user_id=claims.get("user_id")).first() if claims.get("sid") else None
        if self.microsoft_only and (session is None or session.provider_type != "microsoft"):
            return Response({"logged_out": False, "detail": "This session was not started with Microsoft."})
        if session:
            first_logout = session.revoked_at is None
            revoke_session(session.pk)
            if first_logout:
                record_account_activity(session.user, AccountActivity.Action.LOGOUT, "Signed out of the KOT7K ecosystem.", {"sid": str(session.pk)}, request=request)
        try:
            RefreshToken(raw).blacklist()
        except TokenError:
            pass
        # A token from a different browser must never flush this cookie session.
        if session and request.session.get("sso_sid") == str(session.pk):
            session_logout(request)
        return Response(status=204)


class MicrosoftLogoutView(LogoutView):
    microsoft_only = True
