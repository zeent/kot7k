from rest_framework import serializers

from kot7k.organizations.models import IdentityProvider


SENSITIVE_CONFIGURATION_KEYS = {
    "clientsecret",
    "privatekey",
    "secret",
    "token",
    "password",
}


def contains_sensitive_key(value):
    if isinstance(value, dict):
        for key, child in value.items():
            normalized_key = "".join(character for character in key.lower() if character.isalnum())
            if normalized_key in SENSITIVE_CONFIGURATION_KEYS:
                return True
            if contains_sensitive_key(child):
                return True
    elif isinstance(value, list):
        return any(contains_sensitive_key(child) for child in value)
    return False


class IdentityProviderSerializer(serializers.ModelSerializer):
    has_secret_reference = serializers.SerializerMethodField()
    secret = serializers.CharField(write_only=True, required=False, allow_blank=True, trim_whitespace=False)

    class Meta:
        model = IdentityProvider
        fields = (
            "id",
            "key",
            "provider_type",
            "name",
            "is_enabled",
            "display_order",
            "configuration",
            "secret_reference",
            "secret",
            "has_secret_reference",
            "last_tested_at",
            "last_test_status",
            "last_test_error",
            "created_at",
            "updated_at",
            "last_tested_at",
            "last_test_status",
            "last_test_error",
        )
        read_only_fields = (
            "id",
            "has_secret_reference",
            "created_at",
            "updated_at",
        )
        extra_kwargs = {
            "secret_reference": {
                "write_only": True,
                "required": False,
                "allow_blank": True,
            },
        }

    def get_has_secret_reference(self, obj):
        return bool(obj.secret_reference or obj.encrypted_secret)

    def create(self, validated_data):
        secret = validated_data.pop("secret", "")
        instance = super().create(validated_data)
        if secret:
            instance.set_secret(secret)
            instance.save(update_fields=("encrypted_secret",))
        return instance

    def update(self, instance, validated_data):
        secret = validated_data.pop("secret", None)
        instance = super().update(instance, validated_data)
        if secret is not None:
            instance.set_secret(secret)
            instance.save(update_fields=("encrypted_secret",))
        return instance

    def validate_configuration(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Must be a JSON object.")
        if contains_sensitive_key(value):
            raise serializers.ValidationError(
                "Secrets are not allowed here; use secret_reference."
            )
        return value

    def validate_key(self, value):
        providers = IdentityProvider.objects.filter(key=value)
        if self.instance is not None:
            providers = providers.exclude(pk=self.instance.pk)
        if providers.exists():
            raise serializers.ValidationError(
                "This provider key already exists."
            )
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        provider_type = attrs.get("provider_type", getattr(self.instance, "provider_type", None))
        configuration = attrs.get("configuration", getattr(self.instance, "configuration", {}))
        required = {
            IdentityProvider.Type.GOOGLE: ("client_id",),
            IdentityProvider.Type.MICROSOFT: ("client_id", "tenant_id"),
            IdentityProvider.Type.APPLE: ("client_id", "team_id", "key_id"),
            IdentityProvider.Type.OIDC: ("issuer", "client_id"),
            IdentityProvider.Type.LDAP: ("server_uri", "base_dn", "user_filter", "email_attribute"),
            IdentityProvider.Type.X509: ("email_header",),
            IdentityProvider.Type.WEBAUTHN: ("rp_id", "origin"),
        }.get(provider_type, ())
        missing = [key for key in required if not str(configuration.get(key, "")).strip()]
        if missing:
            raise serializers.ValidationError({
                "configuration": f"Missing required settings: {', '.join(missing)}."
            })
        return attrs


class PublicIdentityProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentityProvider
        fields = (
            "key",
            "provider_type",
            "name",
        )
