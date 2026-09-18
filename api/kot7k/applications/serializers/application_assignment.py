from rest_framework import serializers

from kot7k.applications.models import ApplicationAssignment


class ApplicationAssignmentSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    application_name = serializers.CharField(source="application.name", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = ApplicationAssignment
        fields = ("id", "application", "application_name", "user", "user_email", "role", "role_name", "created_at", "updated_at")
        read_only_fields = ("id", "application_name", "user_email", "role_name", "created_at", "updated_at")

    def validate(self, attrs):
        attrs = super().validate(attrs)
        application = attrs.get("application", getattr(self.instance, "application", None))
        role = attrs.get("role", getattr(self.instance, "role", None))
        if application and role and role.application_id != application.id:
            raise serializers.ValidationError({"role": "The role belongs to another application."})
        return attrs
