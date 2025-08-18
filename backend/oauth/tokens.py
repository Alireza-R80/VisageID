import time
import secrets
import jwt
from django.conf import settings
from django.utils import timezone

from .models import Token


def mint_id_token(sub, aud, nonce, auth_time, kid, expires_in=600):
    now = int(time.time())
    payload = {
        "iss": settings.OIDC_ISSUER,
        "sub": sub,
        "aud": aud,
        "iat": now,
        "exp": now + expires_in,
        "nonce": nonce,
        "auth_time": auth_time,
        "acr": "urn:visageid:face:l1",
        "amr": ["face"],
    }
    return jwt.encode(payload, settings.PRIVKEY_PEM, algorithm="RS256", headers={"kid": kid})


def mint_access_token(user, client, scope, expires_in=600):
    token = secrets.token_urlsafe(32)
    now = timezone.now()
    Token.objects.create(
        jti=token,
        user=user,
        client=client,
        type="access",
        scope=scope,
        claims_json={},
        issued_at=now,
        expires_at=now + timezone.timedelta(seconds=expires_in),
    )
    return token


def mint_refresh_token(user, client, scope, expires_in=1209600):
    token = secrets.token_urlsafe(32)
    now = timezone.now()
    Token.objects.create(
        jti=token,
        user=user,
        client=client,
        type="refresh",
        scope=scope,
        claims_json={},
        issued_at=now,
        expires_at=now + timezone.timedelta(seconds=expires_in),
    )
    return token


def verify_access_token(token_str):
    try:
        tok = Token.objects.get(jti=token_str, type="access")
    except Token.DoesNotExist:
        return None
    now = timezone.now()
    if tok.revoked_at or tok.expires_at <= now:
        return None
    return tok
