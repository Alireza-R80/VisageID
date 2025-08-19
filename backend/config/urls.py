from django.contrib import admin
from django.urls import path, include
from oauth.views_discovery import openid_configuration

urlpatterns = [
    path(".well-known/openid-configuration", openid_configuration),
    path("oauth/", include("oauth.urls")),
    path("account/", include("accounts.urls")),
    path("orgs/", include("orgs.urls")),
    path("admin/", admin.site.urls),
]
