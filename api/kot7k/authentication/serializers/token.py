from rest_framework_simplejwt.serializers import TokenRefreshSerializer


class OrganizationTokenRefreshSerializer(TokenRefreshSerializer):
    """Backward-compatible import; tokens are installation-wide now."""
