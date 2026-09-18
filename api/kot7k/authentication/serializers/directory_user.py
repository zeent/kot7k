from django.contrib.auth import get_user_model
from rest_framework import serializers


class DirectoryUserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)

    class Meta:
        model = get_user_model()
        fields = (
            "id", "email", "first_name", "last_name", "full_name",
            "is_active", "is_staff", "password", "date_joined",
        )
        read_only_fields = ("id", "full_name", "date_joined")

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        return self.Meta.model.objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save(update_fields=("password",))
        return instance
