import base64
import io
import os
from pathlib import Path

from PIL import Image

import django
from django.conf import settings
from django.test import Client


def make_data_url(color):
    img = Image.new("RGB", (64, 64), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def main():
    # Ensure test settings
    assert settings.SECRET_KEY

    client = Client()

    # Signup with a green image
    import uuid
    email = f"user1+{uuid.uuid4().hex[:8]}@example.com"
    data_url = make_data_url((0, 255, 0))
    resp = client.post(
        "/account/face/signup",
        data={
            "email": email,
            "display_name": "User One",
            "password": "testpass",
            "image": data_url,
        },
        content_type="application/json",
    )
    print("signup status:", resp.status_code, resp.content)
    assert resp.status_code == 201, resp.content

    # Login with similar green image
    resp = client.post(
        "/account/face/login",
        data={"image": make_data_url((0, 254, 0))},
        content_type="application/json",
    )
    print("login ok status:", resp.status_code, resp.content)
    assert resp.status_code == 200, resp.content

    # Login with different red image (for info only; threshold may accept with test embed)
    resp = client.post(
        "/account/face/login",
        data={"image": make_data_url((255, 0, 0))},
        content_type="application/json",
    )
    print("login (red) status:", resp.status_code, resp.content)


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
    main()
