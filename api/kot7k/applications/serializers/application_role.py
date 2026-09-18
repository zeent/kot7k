from rest_framework import serializers

from kot7k.applications.models import ApplicationRole


class ApplicationRoleSerializer(serializers.ModelSerializer):
    application_name = serializers.CharField(source="application.name", read_only=True)

    class Meta:
        model = ApplicationRole
        fields = ("id", "application", "application_name", "key", "name", "description", "created_at", "updated_at")
        read_only_fields = ("id", "application_name", "created_at", "updated_at")
