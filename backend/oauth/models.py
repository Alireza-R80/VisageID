from django.db import models
from django.conf import settings
from orgs.models import OAuthClient

class AuthSession(models.Model):
    client = models.ForeignKey(OAuthClient, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    state = models.CharField(max_length=255)
    nonce = models.CharField(max_length=255)
    code_challenge = models.CharField(max_length=255)
    code_challenge_method = models.CharField(max_length=10)
    redirect_uri = models.URLField()
    scope = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    verified_face = models.BooleanField(default=False)
    liveness_passed = models.BooleanField(default=False)

class AuthorizationCode(models.Model):
    session = models.ForeignKey(AuthSession, on_delete=models.CASCADE)
    code = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)

class Token(models.Model):
    TYPE_CHOICES = [("access", "access"), ("refresh", "refresh"), ("id", "id")]
    jti = models.CharField(max_length=36, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    client = models.ForeignKey(OAuthClient, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    scope = models.CharField(max_length=255)
    claims_json = models.JSONField(default=dict)
    issued_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
