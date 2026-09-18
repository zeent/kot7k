from kot7k.authentication.views.end_session import EndSessionView
"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path, re_path
from .ui import ui
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from .ui import ui
from kot7k.authentication.views.oidc import (
    AuthorizationView, RevocationView, TokenView, UserInfoView, discovery, jwks,
)

urlpatterns = [
    path("oauth/logout/", EndSessionView.as_view(), name="oidc-logout"),
    path(".well-known/openid-configuration", discovery, name="oidc-discovery"),
    path(".well-known/jwks.json", jwks, name="oidc-jwks"),
    path("oauth/authorize/", AuthorizationView.as_view(), name="oidc-authorize"),
    path("oauth/token/", TokenView.as_view(), name="oidc-token"),
    path("oauth/userinfo/", UserInfoView.as_view(), name="oidc-userinfo"),
    path("oauth/revoke/", RevocationView.as_view(), name="oidc-revoke"),
    path("admin/", admin.site.urls),
    path("api/", include("config.api_urls")),
    # Keep unknown backend URLs out of the frontend, including slash redirects.
    re_path(r"^(?!(?:api|oauth|admin|static|media|\.well-known)(?:/|$))(?P<path>.*)$", ui, name="ui"),
]
