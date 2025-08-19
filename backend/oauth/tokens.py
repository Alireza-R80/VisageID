import time
import secrets
import jwt
from django.conf import settings
from django.utils import timezone

from .models import Token


def _get_kid():
    kid = "dev"
    try:
        jwks = jwt.json.loads(settings.PUBKEY_JWKS) if isinstance(settings.PUBKEY_JWKS, str) else settings.PUBKEY_JWKS
    except Exception:
        jwks = {"keys": []}
    if isinstance(jwks, dict) and jwks.get("keys"):
        kid = jwks["keys"][0].get("kid", "dev")
    return kid


def mint_id_token(sub, aud, nonce, auth_time, kid=None, expires_in=600):
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
    kid = kid or _get_kid()
    return jwt.encode(payload, settings.PRIVKEY_PEM, algorithm="RS256", headers={"kid": kid})


def mint_access_token(user, client, scope, expires_in=600):
    now = timezone.now()
    if getattr(settings, "ACCESS_TOKENS_AS_JWT", False):
        jti = secrets.token_urlsafe(16)
        payload = {
            "iss": settings.OIDC_ISSUER,
            "sub": str(user.id),
            "aud": client.client_id,
            "scope": scope,
            "iat": int(time.time()),
            "exp": int(time.time()) + expires_in,
            "jti": jti,
            "token_use": "access",
        }
        token_str = jwt.encode(payload, settings.PRIVKEY_PEM, algorithm="RS256", headers={"kid": _get_kid()})
        Token.objects.create(
            jti=jti,
            user=user,
            client=client,
            type="access",
            scope=scope,
            claims_json=payload,
            issued_at=now,
            expires_at=now + timezone.timedelta(seconds=expires_in),
        )
        return token_str
    else:
        token = secrets.token_urlsafe(32)
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
    if getattr(settings, "ACCESS_TOKENS_AS_JWT", False):
        # Decode without signature verification just to get jti; rely on DB for validity
        try:
            payload = jwt.decode(token_str, options={"verify_signature": False, "verify_exp": False})
            jti = payload.get("jti")
        except Exception:
            return None
        if not jti:
            return None
        try:
            tok = Token.objects.get(jti=jti, type="access")
        except Token.DoesNotExist:
            return None
    else:
        try:
            tok = Token.objects.get(jti=token_str, type="access")
        except Token.DoesNotExist:
            return None
    now = timezone.now()
    if tok.revoked_at or tok.expires_at <= now:
        return None
    return tok
