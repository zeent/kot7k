from kot7k.applications.views.oauth_client import ApplicationOIDCView, ApplicationOIDCRotateSecretView
from django.urls import path

from kot7k.applications.views import (
    ApplicationAssignmentDetailView,
    ApplicationAssignmentListCreateView,
    ApplicationDetailView,
    ApplicationListCreateView,
    ApplicationRoleDetailView,
    ApplicationRoleListCreateView,
)

app_name = "applications"

urlpatterns = [
    path("<int:pk>/oidc/", ApplicationOIDCView.as_view(), name="application-oidc"),
    path("<int:pk>/oidc/rotate-secret/", ApplicationOIDCRotateSecretView.as_view(), name="application-oidc-rotate"),
    path("", ApplicationListCreateView.as_view(), name="application-list"),
    path("<int:pk>/", ApplicationDetailView.as_view(), name="application-detail"),
    path("roles/", ApplicationRoleListCreateView.as_view(), name="role-list"),
    path("roles/<int:pk>/", ApplicationRoleDetailView.as_view(), name="role-detail"),
    path("assignments/", ApplicationAssignmentListCreateView.as_view(), name="assignment-list"),
    path("assignments/<int:pk>/", ApplicationAssignmentDetailView.as_view(), name="assignment-detail"),
]
