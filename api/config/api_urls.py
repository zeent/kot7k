from django.urls import include, path

from config.api import health
from kot7k.applications.views import DashboardView


app_name = "api"

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("health/",
         health,
         name="health"),
    path("authentication/",
         include("kot7k.authentication.urls"),
         name="authentication"),
    path("identity-providers/",
         include("kot7k.organizations.urls"),
         name="identity-providers"),
    path("applications/",
         include("kot7k.applications.urls"),
         name="applications"),
]
