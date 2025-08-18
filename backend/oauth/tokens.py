import time
import jwt
from django.conf import settings


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
