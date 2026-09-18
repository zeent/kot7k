from kot7k.authentication.views.logout import MicrosoftLogoutView
from kot7k.authentication.views.end_session import LogoutCompleteView
from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView

from kot7k.authentication.views import (
    ExternalLoginCompleteView,
    AppleCallbackView,
    AppleStartView,
    GoogleCallbackView,
    GoogleStartView,
    LoginView,
    LogoutView,
    MeView,
    MicrosoftCallbackView,
    MicrosoftStartView,
    X509CallbackView,
    X509StartView,
    WebAuthnLoginOptionsView,
    WebAuthnLoginVerifyView,
    WebAuthnRegistrationOptionsView,
    WebAuthnRegistrationVerifyView,
    DirectoryUserDetailView,
    DirectoryUserListCreateView,
    GenericOIDCCallbackView,
    GenericOIDCStartView,
)


urlpatterns = [
    path("microsoft/logout/", MicrosoftLogoutView.as_view(), name="microsoft-logout"),
    path("logout/complete/", LogoutCompleteView.as_view(), name="logout-complete"),
    path("oidc/<str:provider_key>/start/", GenericOIDCStartView.as_view(), name="generic-oidc-start"),
    path("oidc/callback/", GenericOIDCCallbackView.as_view(), name="generic-oidc-callback"),
    path("apple/<str:provider_key>/start/", AppleStartView.as_view(), name="apple-start"),
    path("apple/callback/", AppleCallbackView.as_view(), name="apple-callback"),
    path("users/", DirectoryUserListCreateView.as_view(), name="user-list"),
    path("users/<int:pk>/", DirectoryUserDetailView.as_view(), name="user-detail"),
    path("webauthn/<str:provider_key>/register/options/", WebAuthnRegistrationOptionsView.as_view(), name="webauthn-register-options"),
    path("webauthn/<str:provider_key>/register/verify/", WebAuthnRegistrationVerifyView.as_view(), name="webauthn-register-verify"),
    path("webauthn/<str:provider_key>/login/options/", WebAuthnLoginOptionsView.as_view(), name="webauthn-login-options"),
    path("webauthn/<str:provider_key>/login/verify/", WebAuthnLoginVerifyView.as_view(), name="webauthn-login-verify"),
    path("x509/<str:provider_key>/start/", X509StartView.as_view(), name="x509-start"),
    path("x509/callback/", X509CallbackView.as_view(), name="x509-callback"),
    path(
        "microsoft/<str:provider_key>/start/",
        MicrosoftStartView.as_view(),
        name="microsoft-start",
    ),
    path(
        "microsoft/callback/",
        MicrosoftCallbackView.as_view(),
        name="microsoft-callback",
    ),
    path(
        "google/<str:provider_key>/start/",
        GoogleStartView.as_view(),
        name="google-start",
    ),
    path(
        "google/callback/",
        GoogleCallbackView.as_view(),
        name="google-callback",
    ),
    path(
        "external/complete/",
        ExternalLoginCompleteView.as_view(),
        name="external-login-complete",
    ),
    path(
        "login/",
        LoginView.as_view(),
        name="auth-login",
    ),

    path(
        "me/",
        MeView.as_view(),
        name="auth-me",
    ),

    path(
        "logout/",
        LogoutView.as_view(),
        name="auth-logout",
    ),

    path(
        "refresh/",
        TokenRefreshView.as_view(),
        name="auth-refresh",
    ),
]
