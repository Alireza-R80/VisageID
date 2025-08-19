import base64
import hashlib
import io
import json
import os
from urllib.parse import urlparse, parse_qs

from PIL import Image
import django
from django.test import Client


def data_url(color):
    img = Image.new("RGB", (64, 64), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def main():
    from accounts.models import User, FaceEmbedding
    from facekit.adapter import FaceAdapter
    from orgs.models import Organization, OAuthClient

    c = Client()

    # Create user and enroll embedding
    user = User.objects.create_user(email="oauth@example.com", password=None, display_name="OAuth User")
    adapter = FaceAdapter()
    img = Image.new("RGB", (64, 64), color=(0, 200, 0))
    import numpy as np
    bgr = np.array(img)[:, :, ::-1]
    FaceEmbedding.objects.create(user=user, model_name="default", vector=adapter.embed_and_encrypt(bgr))

    # Create org and confidential client
    org = Organization.objects.create(name="Test Org", owner=user)
    secret_plain = "s3cr3t-123"
    client = OAuthClient.objects.create(
        org=org,
        name="Test Client",
        redirect_uris=["https://example.com/cb"],
        post_logout_redirect_uris=["https://example.com/logout"],
        is_confidential=True,
        pkce_enforced=True,
        client_secret_hash=hashlib.sha256(secret_plain.encode()).hexdigest(),
    )

    # Simulate authorize verify (final step): should 302 redirect with code
    payload = {
        "client_id": client.client_id,
        "state": "abc123",
        "redirect_uri": "https://example.com/cb",
        "nonce": "n",
        "code_challenge": "verifier",  # using plain
        "code_challenge_method": "plain",
        "scope": "openid profile email",
        "image": data_url((0, 200, 0)),
    }
    resp = c.post("/oauth/authorize/verify", data=json.dumps(payload), content_type="application/json", follow=False)
    print("authorize/verify status:", resp.status_code)
    assert resp.status_code in (301, 302), resp.content
    loc = resp["Location"]
    print("redirect:", loc)
    qs = parse_qs(urlparse(loc).query)
    code = qs.get("code", [None])[0]
    assert code, "missing code"

    # Exchange token with client auth and PKCE
    basic = base64.b64encode(f"{client.client_id}:{secret_plain}".encode()).decode()
    token_body = {
        "grant_type": "authorization_code",
        "code": code,
        "code_verifier": "verifier",
    }
    resp = c.post("/oauth/token", data=json.dumps(token_body), content_type="application/json", HTTP_AUTHORIZATION=f"Basic {basic}")
    print("token status:", resp.status_code, resp.content)
    assert resp.status_code == 200, resp.content
    tok = json.loads(resp.content.decode())
    assert tok.get("access_token"), tok
    assert tok.get("id_token"), tok

    # Call userinfo
    resp = c.get("/oauth/userinfo", HTTP_AUTHORIZATION=f"Bearer {tok['access_token']}")
    print("userinfo status:", resp.status_code, resp.content)
    assert resp.status_code == 200, resp.content


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    main()

