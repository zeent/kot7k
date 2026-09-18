from kot7k.authentication.services.sso import begin_session
import secrets

from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from webauthn import generate_authentication_options, generate_registration_options, verify_authentication_response, verify_registration_response
from webauthn.helpers.exceptions import InvalidAuthenticationResponse, InvalidRegistrationResponse
from webauthn.helpers.structs import AuthenticatorSelectionCriteria, ResidentKeyRequirement, UserVerificationRequirement

from kot7k.authentication.models import AccountActivity, WebAuthnCredential
from kot7k.authentication.services.account_activity import record_account_activity
from kot7k.authentication.serializers import MeSerializer
from kot7k.authentication.services.webauthn import credential_descriptors, encode_base64url, provider_settings, public_options
from kot7k.organizations.models import IdentityProvider


def _provider(request, provider_key):
    return IdentityProvider.objects.filter(key=provider_key, provider_type=IdentityProvider.Type.WEBAUTHN, is_enabled=True).first()


def _key(kind, token):
    return f"webauthn:{kind}:{token}"


def _session(user, request=None):
    if request is not None:
        record_account_activity(
            user, AccountActivity.Action.LOGIN, "Signed in to KOT7K.",
            {"method": "webauthn"},
            request=request,
        )
    refresh = begin_session(request, user, "webauthn")
    data = MeSerializer(user).data
    return {"access": str(refresh.access_token), "refresh": str(refresh), "user": data}


class WebAuthnRegistrationOptionsView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, provider_key):
        provider = _provider(request, provider_key)
        if provider is None:
            return Response({"detail": "Passkey provider not found."}, status=404)
        try:
            rp_id, rp_name, _ = provider_settings(provider)
        except ImproperlyConfigured as exc:
            return Response({"detail": str(exc)}, status=500)
        options = generate_registration_options(
            rp_id=rp_id, rp_name=rp_name, user_name=request.user.email,
            user_id=str(request.user.id).encode(),
            user_display_name=request.user.get_full_name() or request.user.email,
            exclude_credentials=credential_descriptors(WebAuthnCredential.objects.filter(provider=provider, user=request.user)),
            authenticator_selection=AuthenticatorSelectionCriteria(resident_key=ResidentKeyRequirement.REQUIRED, require_resident_key=True, user_verification=UserVerificationRequirement.REQUIRED),
        )
        token = secrets.token_urlsafe(32)
        cache.set(_key("register", token), {"challenge": options.challenge, "provider_id": provider.id, "user_id": request.user.id}, 300)
        return Response({"flow_token": token, "public_key": public_options(options)})


class WebAuthnRegistrationVerifyView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, provider_key):
        token = request.data.get("flow_token", "")
        key = _key("register", token)
        flow = cache.get(key)
        cache.delete(key)
        provider = _provider(request, provider_key)
        if not flow or provider is None or flow["provider_id"] != provider.id or flow["user_id"] != request.user.id:
            return Response({"detail": "Invalid or expired passkey registration."}, status=400)
        try:
            rp_id, _, origins = provider_settings(provider)
            verified = verify_registration_response(credential=request.data.get("credential", {}), expected_challenge=flow["challenge"], expected_rp_id=rp_id, expected_origin=origins, require_user_verification=True)
        except (InvalidRegistrationResponse, ImproperlyConfigured, ValueError) as exc:
            return Response({"detail": str(exc)}, status=400)
        credential, created = WebAuthnCredential.objects.get_or_create(
            provider=provider, credential_id=encode_base64url(verified.credential_id),
            defaults={"user": request.user, "public_key": verified.credential_public_key, "sign_count": verified.sign_count,
                      "transports": request.data.get("credential", {}).get("response", {}).get("transports", []), "name": (request.data.get("name") or "Passkey")[:100]},
        )
        if credential.user_id != request.user.id:
            return Response({"detail": "This passkey is already registered."}, status=409)
        return Response({"id": credential.id, "name": credential.name}, status=201 if created else 200)


class WebAuthnLoginOptionsView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request, provider_key):
        provider = _provider(request, provider_key)
        if provider is None:
            return Response({"detail": "Passkey provider not found."}, status=404)
        try:
            rp_id, _, _ = provider_settings(provider)
        except ImproperlyConfigured as exc:
            return Response({"detail": str(exc)}, status=500)
        options = generate_authentication_options(rp_id=rp_id, user_verification=UserVerificationRequirement.REQUIRED)
        token = secrets.token_urlsafe(32)
        cache.set(_key("login", token), {"challenge": options.challenge, "provider_id": provider.id}, 300)
        return Response({"flow_token": token, "public_key": public_options(options)})


class WebAuthnLoginVerifyView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request, provider_key):
        token = request.data.get("flow_token", "")
        key = _key("login", token)
        flow = cache.get(key)
        cache.delete(key)
        provider = _provider(request, provider_key)
        raw = request.data.get("credential", {})
        credential = WebAuthnCredential.objects.select_related("user").filter(provider=provider, credential_id=raw.get("id", "")).first()
        if not flow or provider is None or flow["provider_id"] != provider.id or credential is None:
            return Response({"detail": "Invalid or expired passkey login."}, status=400)
        if not credential.user.is_active:
            return Response({"detail": "Active user account required."}, status=403)
        try:
            rp_id, _, origins = provider_settings(provider)
            verified = verify_authentication_response(credential=raw, expected_challenge=flow["challenge"], expected_rp_id=rp_id, expected_origin=origins, credential_public_key=bytes(credential.public_key), credential_current_sign_count=credential.sign_count, require_user_verification=True)
        except (InvalidAuthenticationResponse, ImproperlyConfigured, ValueError) as exc:
            return Response({"detail": str(exc)}, status=401)
        credential.sign_count = verified.new_sign_count
        credential.last_used_at = timezone.now()
        credential.save(update_fields=("sign_count", "last_used_at", "updated_at"))
        return Response(_session(credential.user, request))
