from django.contrib.auth import logout
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .services.sso import active_session


class SessionJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if not active_session(validated_token.get("sid"), user.pk):
            raise InvalidToken("Session expired or signed out. Sign in again.")
        return user


class SessionTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        token = RefreshToken(attrs["refresh"])
        if not active_session(token.get("sid"), token.get("user_id")):
            raise InvalidToken("Session expired or signed out. Sign in again.")
        return super().validate(attrs)


class SSOSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        sid = request.session.get("sso_sid")
        if sid and not active_session(sid):
            logout(request)
        return self.get_response(request)
