import secrets
from django.db import models
from django.conf import settings


def generate_client_id():
    return secrets.token_hex(16)

class Organization(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class OAuthClient(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    client_id = models.CharField(max_length=32, unique=True, default=generate_client_id)
    client_secret_hash = models.CharField(max_length=128)
    redirect_uris = models.JSONField(default=list)
    post_logout_redirect_uris = models.JSONField(default=list)
    is_confidential = models.BooleanField(default=True)
    pkce_enforced = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
