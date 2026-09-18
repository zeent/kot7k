from kot7k.authentication.services.sso import begin_session
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


from kot7k.authentication.serializers import LoginSerializer, MeSerializer
from kot7k.organizations.models import IdentityProvider
from kot7k.authentication.services.ldap import authenticate_ldap
from kot7k.authentication.models import AccountActivity
from kot7k.authentication.services.account_activity import record_account_activity


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()

        password = (
            serializer.validated_data.get("password") or ""
        )

        password_providers = IdentityProvider.objects.filter(
            provider_type__in=(IdentityProvider.Type.LOCAL, IdentityProvider.Type.LDAP),
            is_enabled=True,
        )
        # Bootstrap access when no identity provider is enabled. An enabled
        # external provider still controls whether password login is offered.
        use_local_fallback = not IdentityProvider.objects.filter(is_enabled=True).exists()
        if not use_local_fallback and not password_providers.exists():
            return Response(
                {"detail": "Email and password login is not enabled."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not email or not password:
            return Response(
                {"detail": "Missing credentials"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = None
        provider_type, provider_key = "local", ""
        if use_local_fallback or password_providers.filter(provider_type=IdentityProvider.Type.LOCAL).exists():
            user = authenticate(request=request, email=email, password=password)
        if user is None:
            for provider in password_providers.filter(provider_type=IdentityProvider.Type.LDAP):
                user = authenticate_ldap(provider, email, password)
                if user is not None:
                    provider_type, provider_key = "ldap", provider.key
                    break

        if user is None:
            return Response(
                {
                    "detail": "Invalid email or password"
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = begin_session(request, user, provider_type=provider_type, provider_key=provider_key)
        record_account_activity(
            user, AccountActivity.Action.LOGIN, "Signed in to KOT7K.",
            {"method": "password"},
            request=request,
        )
        user_data = MeSerializer(user).data

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": user_data,
            },
            status=status.HTTP_200_OK,
        )
