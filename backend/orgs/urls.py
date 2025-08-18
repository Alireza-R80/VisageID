from django.urls import path

from .views import OAuthClientViewSet, oauth_client_dashboard

oauthclient_list = OAuthClientViewSet.as_view({"get": "list", "post": "create"})
oauthclient_detail = OAuthClientViewSet.as_view({"delete": "destroy"})
oauthclient_rotate = OAuthClientViewSet.as_view({"post": "rotate_secret"})

urlpatterns = [
    path("<int:org_pk>/oauth-clients/", oauthclient_list, name="oauthclient-list"),
    path("<int:org_pk>/oauth-clients/<int:pk>/", oauthclient_detail, name="oauthclient-detail"),
    path(
        "<int:org_pk>/oauth-clients/<int:pk>/rotate-secret/",
        oauthclient_rotate,
        name="oauthclient-rotate",
    ),
    path("<int:org_pk>/dashboard/", oauth_client_dashboard, name="org-dashboard"),
]
