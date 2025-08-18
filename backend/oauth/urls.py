from django.urls import path
from .views_discovery import openid_configuration
from . import views

urlpatterns = [
    path(".well-known/openid-configuration", openid_configuration),
    path("jwks.json", views.jwks),
    path("authorize", views.authorize),
    path("authorize/verify", views.authorize_verify),
    path("token", views.token),
    path("userinfo", views.userinfo),
    path("revoke", views.revoke),
    path("introspect", views.introspect),
]
