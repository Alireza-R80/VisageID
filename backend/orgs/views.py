import hashlib
import secrets

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Organization, OAuthClient
from .permissions import IsOrgAdmin
from .serializers import OAuthClientSerializer, OAuthClientCreateSerializer


def _generate_secret():
    secret = secrets.token_urlsafe(32)
    secret_hash = hashlib.sha256(secret.encode()).hexdigest()
    return secret, secret_hash


class OAuthClientViewSet(viewsets.ModelViewSet):
    """API endpoints for managing OAuth clients within an organization."""

    permission_classes = [IsOrgAdmin]
    queryset = OAuthClient.objects.all()

    def get_queryset(self):
        return OAuthClient.objects.filter(org_id=self.kwargs["org_pk"])

    def get_serializer_class(self):
        if self.action == "create":
            return OAuthClientCreateSerializer
        return OAuthClientSerializer

    def perform_create(self, serializer):
        secret, secret_hash = _generate_secret()
        serializer.save(org_id=self.kwargs["org_pk"], client_secret_hash=secret_hash)
        self._plain_secret = secret

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data["client_secret"] = getattr(self, "_plain_secret", None)
        return response

    @action(detail=True, methods=["post"])
    def rotate_secret(self, request, *args, **kwargs):
        client = self.get_object()
        secret, secret_hash = _generate_secret()
        client.client_secret_hash = secret_hash
        client.save()
        return Response({"client_id": client.client_id, "client_secret": secret})


@login_required
def oauth_client_dashboard(request, org_pk):
    """Simple dashboard for viewing and rotating OAuth client secrets."""

    org = get_object_or_404(Organization, pk=org_pk, owner=request.user)
    context = {"org": org, "clients": org.oauthclient_set.all()}

    if request.method == "POST":
        client = get_object_or_404(OAuthClient, pk=request.POST.get("client_id"), org=org)
        secret, secret_hash = _generate_secret()
        client.client_secret_hash = secret_hash
        client.save()
        context["rotated_secret"] = secret

    return render(request, "orgs/client_dashboard.html", context)
