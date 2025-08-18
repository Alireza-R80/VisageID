from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from rest_framework import serializers

from .models import OAuthClient


class OAuthClientSerializer(serializers.ModelSerializer):
    """Serializer for listing OAuth clients."""

    class Meta:
        model = OAuthClient
        fields = [
            "id",
            "name",
            "client_id",
            "redirect_uris",
            "post_logout_redirect_uris",
            "is_confidential",
            "pkce_enforced",
            "created_at",
        ]
        read_only_fields = ["id", "client_id", "created_at"]

    def _validate_uri_list(self, value):
        validator = URLValidator()
        for uri in value:
            try:
                validator(uri)
            except ValidationError:
                raise serializers.ValidationError(f"Invalid URL: {uri}")
        return value

    def validate_redirect_uris(self, value):
        return self._validate_uri_list(value)

    def validate_post_logout_redirect_uris(self, value):
        return self._validate_uri_list(value)


class OAuthClientCreateSerializer(OAuthClientSerializer):
    """Serializer for creating OAuth clients."""

    class Meta(OAuthClientSerializer.Meta):
        fields = [
            "id",
            "name",
            "redirect_uris",
            "post_logout_redirect_uris",
            "is_confidential",
            "pkce_enforced",
        ]
        read_only_fields = ["id"]
