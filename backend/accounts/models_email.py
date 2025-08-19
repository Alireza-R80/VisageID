from django.db import models
from django.conf import settings
from django.utils import timezone


class EmailVerificationToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def create_for(cls, user, ttl_seconds=3600):
        import secrets
        t = secrets.token_urlsafe(32)
        return cls.objects.create(
            user=user,
            token=t,
            expires_at=timezone.now() + timezone.timedelta(seconds=ttl_seconds),
        )

