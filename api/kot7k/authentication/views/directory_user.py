from django.contrib.auth import get_user_model
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.exceptions import ValidationError

from kot7k.authentication.serializers.directory_user import DirectoryUserSerializer
from kot7k.organizations.permissions import IsPlatformAdmin


class DirectoryUserListCreateView(ListCreateAPIView):
    queryset = get_user_model().objects.order_by("email")
    serializer_class = DirectoryUserSerializer
    permission_classes = (IsPlatformAdmin,)


class DirectoryUserDetailView(RetrieveUpdateDestroyAPIView):
    queryset = get_user_model().objects.order_by("email")
    serializer_class = DirectoryUserSerializer
    permission_classes = (IsPlatformAdmin,)

    def perform_destroy(self, instance):
        if instance.pk == self.request.user.pk:
            raise ValidationError("You cannot delete your own account.")
        instance.delete()
