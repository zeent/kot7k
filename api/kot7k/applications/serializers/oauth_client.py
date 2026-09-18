from urllib.parse import urlsplit
from rest_framework import serializers
from kot7k.applications.models import OAuthClient


class OAuthClientSerializer(serializers.ModelSerializer):
    redirect_uris = serializers.ListField(child=serializers.CharField(max_length=2048), allow_empty=False)
    allowed_scopes = serializers.ListField(child=serializers.ChoiceField(choices=['openid', 'email', 'profile', 'roles', 'offline_access']), allow_empty=False)

    class Meta:
        model = OAuthClient
        fields = ('client_id', 'is_confidential', 'redirect_uris', 'allowed_scopes', 'is_active')
        read_only_fields = ('client_id',)

    def validate_redirect_uris(self, values):
        for value in values:
            try:
                url = urlsplit(value)
                valid = (url.hostname and not url.username and not url.password and not url.fragment
                         and not any(c.isspace() for c in value) and '\\' not in value and '*' not in value
                         and (url.scheme == 'https' or (url.scheme == 'http' and url.hostname in ('localhost', '127.0.0.1', '::1'))))
                url.port
            except ValueError:
                valid = False
            if not valid:
                raise serializers.ValidationError('Use absolute HTTPS callback URLs, or HTTP on localhost; no fragments or wildcards.')
        return list(dict.fromkeys(values))

    def validate_allowed_scopes(self, values):
        if 'openid' not in values:
            raise serializers.ValidationError('The openid scope is required.')
        return list(dict.fromkeys(values))
