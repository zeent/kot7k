from django.conf import settings

from kot7k.authentication.models import AccountActivity


def request_ip_address(request):
    if request is None:
        return None
    if settings.TRUST_X_FORWARDED_FOR:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            return forwarded.split(",", 1)[0].strip()
    return request.META.get("REMOTE_ADDR") or None


def record_account_activity(user, action, description, metadata=None, request=None):
    return AccountActivity.objects.create(
        user=user, action=action, description=description, metadata=metadata or {},
        ip_address=request_ip_address(request),
    )
