from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from kot7k.applications.models import ApplicationAssignment
from kot7k.applications.serializers import ApplicationAssignmentSerializer
from kot7k.organizations.permissions import IsPlatformAdmin


class ApplicationAssignmentQuerysetMixin:
    def get_queryset(self):
        queryset = ApplicationAssignment.objects.select_related(
            "application", "user", "role"
        )
        application_id = self.request.query_params.get("application")
        return queryset.filter(application_id=application_id) if application_id else queryset


class ApplicationAssignmentListCreateView(ApplicationAssignmentQuerysetMixin, ListCreateAPIView):
    serializer_class = ApplicationAssignmentSerializer
    permission_classes = (IsPlatformAdmin,)


class ApplicationAssignmentDetailView(ApplicationAssignmentQuerysetMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = ApplicationAssignmentSerializer
    permission_classes = (IsPlatformAdmin,)
