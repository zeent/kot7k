from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from kot7k.organizations.models import IdentityProvider
from kot7k.organizations.permissions import IsPlatformAdmin
from kot7k.organizations.serializers import IdentityProviderSerializer
from kot7k.organizations.serializers.identity_provider import PublicIdentityProviderSerializer
from kot7k.organizations.services import IdentityProviderConnectionError, test_provider
from django.utils import timezone
from django.shortcuts import get_object_or_404


class IdentityProviderQuerysetMixin:
    def get_queryset(self):
        return IdentityProvider.objects.all()


class IdentityProviderListCreateView(
    IdentityProviderQuerysetMixin,
    ListCreateAPIView,
):
    serializer_class = IdentityProviderSerializer
    permission_classes = (IsPlatformAdmin,)


class IdentityProviderDetailView(
    IdentityProviderQuerysetMixin,
    RetrieveUpdateDestroyAPIView,
):
    serializer_class = IdentityProviderSerializer
    permission_classes = (IsPlatformAdmin,)


class IdentityProviderTestView(APIView):
    permission_classes = (IsPlatformAdmin,)

    def post(self, request, pk):
        provider = get_object_or_404(IdentityProvider, pk=pk)
        provider.last_tested_at = timezone.now()
        try:
            detail = test_provider(provider)
            provider.last_test_status = IdentityProvider.TestStatus.SUCCESS
            provider.last_test_error = ""
            response_status = status.HTTP_200_OK
        except IdentityProviderConnectionError as exc:
            detail = str(exc)
            provider.last_test_status = IdentityProvider.TestStatus.ERROR
            provider.last_test_error = detail
            response_status = status.HTTP_400_BAD_REQUEST
        provider.save(update_fields=("last_tested_at", "last_test_status", "last_test_error"))
        return Response({"status": provider.last_test_status, "detail": detail}, status=response_status)


class IdentityProviderDiscoveryView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def get(self, request):
        providers = IdentityProvider.objects.filter(is_enabled=True)
        data = PublicIdentityProviderSerializer(providers, many=True).data
        if not data:
            data = [{"key": "django-local", "provider_type": "local", "name": "Django"}]
        return Response(data)
