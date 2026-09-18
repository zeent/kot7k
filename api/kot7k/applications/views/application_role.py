from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from kot7k.applications.models import ApplicationRole
from kot7k.applications.serializers import ApplicationRoleSerializer
from kot7k.organizations.permissions import IsPlatformAdmin


class ApplicationRoleQuerysetMixin:
    def get_queryset(self):
        queryset = ApplicationRole.objects.select_related("application")
        application_id = self.request.query_params.get("application")
        return queryset.filter(application_id=application_id) if application_id else queryset


class ApplicationRoleListCreateView(ApplicationRoleQuerysetMixin, ListCreateAPIView):
    serializer_class = ApplicationRoleSerializer
    permission_classes = (IsPlatformAdmin,)


class ApplicationRoleDetailView(ApplicationRoleQuerysetMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = ApplicationRoleSerializer
    permission_classes = (IsPlatformAdmin,)
