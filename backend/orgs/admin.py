from django.contrib import admin
from .models import Organization, OAuthClient

admin.site.register(Organization)
admin.site.register(OAuthClient)
