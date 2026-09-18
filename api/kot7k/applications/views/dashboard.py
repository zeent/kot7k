from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from kot7k.applications.models import Application, ApplicationAssignment
from kot7k.authentication.models import AccountActivity
from kot7k.organizations.models import IdentityProvider


class DashboardView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        assignments = ApplicationAssignment.objects.filter(
            user=request.user, application__is_active=True
        ).select_related("application", "role")
        applications = {}
        for assignment in assignments:
            item = applications.setdefault(assignment.application_id, {
                "id": assignment.application_id,
                "key": assignment.application.key,
                "name": assignment.application.name,
                "description": assignment.application.description,
                "homepage_url": assignment.application.homepage_url,
                "roles": [],
            })
            item["roles"].append({"key": assignment.role.key, "name": assignment.role.name})

        if request.user.is_superuser:
            for application in Application.objects.filter(is_active=True):
                applications.setdefault(application.id, {
                    "id": application.id,
                    "key": application.key,
                    "name": application.name,
                    "description": application.description,
                    "homepage_url": application.homepage_url,
                    "roles": [],
                })

        visible_applications = list(applications.values())
        if request.user.is_superuser:
            visible_applications.insert(0, {
                "id": 0,
                "key": "kot7k-administration",
                "name": "KOT7K Administration",
                "description": "Manage users, applications, roles, and identity providers.",
                "homepage_url": "/administration",
                "roles": [{"key": "platform-administrator", "name": "Platform administrator"}],
            })

        activities = AccountActivity.objects.filter(user=request.user)
        return Response({
            "metrics": {
                "users": get_user_model().objects.filter(is_active=True).count(),
                # KOT7K itself is an internal application and is not stored in
                # the application directory, so it is included explicitly.
                "applications": Application.objects.filter(is_active=True).count() + 1,
                "identity_providers": IdentityProvider.objects.filter(is_enabled=True).count(),
            },
            "applications": visible_applications,
            "activities": [{
                "id": activity.id,
                "action": activity.action,
                "description": activity.description,
                "metadata": activity.metadata,
                "ip_address": activity.ip_address,
                "created_at": activity.created_at,
            } for activity in activities],
        })
