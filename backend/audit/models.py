from django.db import models
from django.conf import settings
from orgs.models import Organization, OAuthClient

class AuditLog(models.Model):
    event = models.CharField(max_length=255)
    ip = models.GenericIPAddressField()
    ua = models.CharField(max_length=255)
    org = models.ForeignKey(Organization, null=True, on_delete=models.SET_NULL)
    client = models.ForeignKey(OAuthClient, null=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    meta_json = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
