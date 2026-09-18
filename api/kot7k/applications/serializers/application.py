from rest_framework import serializers

from kot7k.applications.models import Application


class ApplicationLocationField(serializers.CharField):
    """Application links may point to an internal route or a full web URL."""

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        if value.startswith("/") and not value.startswith("//") and "\\" not in value and not any(character.isspace() for character in value):
            return value
        return serializers.URLField().run_validation(value)


class ApplicationSerializer(serializers.ModelSerializer):
    homepage_url = ApplicationLocationField(max_length=200, allow_blank=True, required=False)

    class Meta:
        model = Application
        fields = ("id", "key", "name", "description", "homepage_url", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")
