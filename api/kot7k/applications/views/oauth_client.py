import secrets
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from kot7k.applications.models import Application, OAuthClient
from kot7k.applications.serializers.oauth_client import OAuthClientSerializer
from kot7k.organizations.permissions import IsPlatformAdmin


def private_response(data, status=200):
    return Response(data, status=status, headers={'Cache-Control': 'no-store', 'Pragma': 'no-cache'})


class ApplicationOIDCView(APIView):
    permission_classes = (IsPlatformAdmin,)

    def get(self, request, pk):
        application = get_object_or_404(Application, pk=pk)
        client = OAuthClient.objects.filter(application=application).first()
        return private_response(OAuthClientSerializer(client).data if client else None)

    @transaction.atomic
    def put(self, request, pk):
        application = get_object_or_404(Application.objects.select_for_update(), pk=pk)
        client = OAuthClient.objects.filter(application=application).first()
        serializer = OAuthClientSerializer(client, data=request.data)
        serializer.is_valid(raise_exception=True)
        needs_secret = serializer.validated_data.get('is_confidential', client.is_confidential if client else True) and (client is None or not client.client_secret_hash)
        client = serializer.save(application=application)
        raw_secret = secrets.token_urlsafe(48) if needs_secret else None
        if raw_secret:
            client.set_secret(raw_secret)
        elif not client.is_confidential:
            client.client_secret_hash = ''
        client.save(update_fields=('client_secret_hash', 'updated_at'))
        data = dict(OAuthClientSerializer(client).data)
        if raw_secret:
            data['client_secret'] = raw_secret
        return private_response(data)


class ApplicationOIDCRotateSecretView(APIView):
    permission_classes = (IsPlatformAdmin,)

    @transaction.atomic
    def post(self, request, pk):
        get_object_or_404(Application.objects.select_for_update(), pk=pk)
        client = get_object_or_404(OAuthClient, application_id=pk)
        if not client.is_confidential:
            return private_response({'detail': 'Public clients do not use a secret.'}, status=400)
        raw_secret = secrets.token_urlsafe(48)
        client.set_secret(raw_secret)
        client.save(update_fields=('client_secret_hash', 'updated_at'))
        return private_response({'client_secret': raw_secret})
