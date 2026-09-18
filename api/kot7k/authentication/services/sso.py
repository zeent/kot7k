from datetime import timedelta
from urllib.parse import urlsplit
import uuid

import requests
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from kot7k.authentication.models import SSOSession, SessionApplication, LogoutDelivery


def validate_logout_uri(uri):
    if not isinstance(uri, str):
        raise ValidationError("Logout URI must be a string.")
    if any(ord(character) <= 32 for character in uri) or "\\" in uri:
        raise ValidationError("Invalid logout URL.")
    try:
        parsed = urlsplit(uri)
        parsed.port
    except ValueError as exc:
        raise ValidationError("Invalid logout URL.") from exc
    local = settings.DEBUG and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if not parsed.hostname or parsed.username or parsed.password or parsed.fragment or not (
        parsed.scheme == "https" or (local and parsed.scheme == "http")
    ):
        raise ValidationError("Logout URLs require HTTPS (HTTP loopback allowed only in development).")


def active_session(sid, user_id=None):
    try:
        query = SSOSession.objects.filter(pk=uuid.UUID(str(sid)), revoked_at__isnull=True, expires_at__gt=timezone.now())
    except (ValueError, TypeError, AttributeError):
        return None
    if user_id is not None:
        query = query.filter(user_id=user_id)
    return query.first()


def browser_session(request):
    sid = request.session.get("sso_sid")
    if sid:
        return active_session(sid, request.user.pk)
    # Upgrade a pre-existing Django login once, without affecting other devices.
    session = SSOSession.objects.create(user=request.user, django_session_key=request.session.session_key or "", expires_at=request.session.get_expiry_date())
    request.session["sso_sid"] = str(session.pk)
    return session


def begin_session(request, user, provider_type="local", provider_key=""):
    old_sid = request.session.get("sso_sid")
    if old_sid:
        revoke_session(old_sid)
        logout(request)
    login(request, user)
    session = SSOSession.objects.create(
        user=user, provider_type=provider_type, provider_key=provider_key,
        django_session_key=request.session.session_key or "",
        expires_at=request.session.get_expiry_date(),
    )
    request.session["sso_sid"] = str(session.pk)
    refresh = RefreshToken.for_user(user)
    refresh["sid"] = str(session.pk)
    return refresh


@transaction.atomic
def revoke_session(sid):
    try:
        session = SSOSession.objects.select_for_update().filter(pk=uuid.UUID(str(sid))).first()
    except (ValueError, TypeError, AttributeError):
        return None
    if session is None or session.revoked_at:
        return session
    session.revoked_at = timezone.now()
    session.save(update_fields=("revoked_at",))
    from kot7k.applications.models import AuthorizationCode, OAuthRefreshToken
    AuthorizationCode.objects.filter(session=session, used_at__isnull=True).update(used_at=session.revoked_at)
    OAuthRefreshToken.objects.filter(session=session, revoked_at__isnull=True).update(revoked_at=session.revoked_at)
    if session.django_session_key:
        Session.objects.filter(session_key=session.django_session_key).delete()
    for participant in SessionApplication.objects.filter(session=session).select_related("client"):
        if participant.client.backchannel_logout_uri:
            LogoutDelivery.objects.get_or_create(session=session, client=participant.client, defaults={"endpoint": participant.client.backchannel_logout_uri})
    # Notification failure never rolls back local revocation. Retry via command.
    transaction.on_commit(lambda: deliver_pending(session_id=session.pk))
    return session


def deliver_pending(session_id=None, limit=100):
    from kot7k.authentication.services.oidc_provider import _sign, issuer
    deliveries = LogoutDelivery.objects.filter(delivered_at__isnull=True)
    if session_id:
        deliveries = deliveries.filter(session_id=session_id)
    count = 0
    for item in deliveries.select_related("session__user", "client").order_by("pk")[:limit]:
        item.attempts += 1
        try:
            validate_logout_uri(item.endpoint)
            now = timezone.now()
            token = _sign({
                "iss": issuer(), "aud": item.client.client_id,
                "sub": str(item.session.user.oidc_subject), "sid": str(item.session_id),
                "iat": int(now.timestamp()), "exp": int((now + timedelta(minutes=2)).timestamp()),
                "jti": str(uuid.uuid4()),
                "events": {"http://schemas.openid.net/event/backchannel-logout": {}},
            })
            response = requests.post(item.endpoint, data={"logout_token": token}, timeout=5, allow_redirects=False)
            if response.status_code != 200:
                raise ValueError(f"HTTP {response.status_code}")
            item.delivered_at = now
            item.last_error = ""
            count += 1
        except Exception as exc:
            # Never persist response bodies, URLs with secrets or token material.
            item.last_error = type(exc).__name__
        item.save(update_fields=("attempts", "delivered_at", "last_error"))
    return count
