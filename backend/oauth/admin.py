from django.contrib import admin
from .models import AuthSession, AuthorizationCode, Token

admin.site.register(AuthSession)
admin.site.register(AuthorizationCode)
admin.site.register(Token)
