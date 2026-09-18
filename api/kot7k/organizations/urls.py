from django.urls import path

from kot7k.organizations.views import (
    IdentityProviderDetailView,
    IdentityProviderDiscoveryView,
    IdentityProviderListCreateView,
    IdentityProviderTestView,
)


app_name = "identity_providers"

urlpatterns = [
    path("", IdentityProviderListCreateView.as_view(), name="list"),
    path("discovery/", IdentityProviderDiscoveryView.as_view(), name="discovery"),
    path("<int:pk>/", IdentityProviderDetailView.as_view(), name="detail"),
    path("<int:pk>/test/", IdentityProviderTestView.as_view(), name="test"),
]
