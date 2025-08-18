from django.http import JsonResponse
from django.conf import settings


def openid_configuration(request):
    base = settings.OIDC_ISSUER
    return JsonResponse({
        "issuer": base,
        "authorization_endpoint": f"{base}/oauth/authorize",
        "token_endpoint": f"{base}/oauth/token",
        "userinfo_endpoint": f"{base}/oauth/userinfo",
        "jwks_uri": f"{base}/oauth/jwks.json",
        "response_types_supported": ["code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "scopes_supported": ["openid", "profile", "email"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post", "none"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "claims_supported": ["sub", "name", "email", "picture", "email_verified"],
    })
