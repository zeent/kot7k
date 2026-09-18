from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from kot7k.applications.models import Application
from kot7k.applications.serializers import ApplicationSerializer
from kot7k.organizations.permissions import IsPlatformAdmin


class ApplicationQuerysetMixin:
    def get_queryset(self):
        return Application.objects.all()


class ApplicationListCreateView(ApplicationQuerysetMixin, ListCreateAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = (IsPlatformAdmin,)


class ApplicationDetailView(ApplicationQuerysetMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = (IsPlatformAdmin,)
