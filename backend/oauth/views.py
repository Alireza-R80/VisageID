import base64
import hashlib
import io
import json
import secrets

import numpy as np
from PIL import Image
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import AuthSession, AuthorizationCode
from orgs.models import OAuthClient
from accounts.models import User
from facekit.adapter import FaceAdapter
from facekit.liveness import LivenessChecker
from . import tokens

adapter = FaceAdapter()
liveness = LivenessChecker()

def jwks(request):
    return JsonResponse(json.loads(settings.PUBKEY_JWKS))

@csrf_exempt
def authorize(request):
    if request.method != "GET":
        return HttpResponseBadRequest("GET required")
    params = {
        "client_id": request.GET.get("client_id", ""),
        "state": request.GET.get("state", ""),
        "redirect_uri": request.GET.get("redirect_uri", ""),
        "nonce": request.GET.get("nonce", ""),
        "code_challenge": request.GET.get("code_challenge", ""),
        "code_challenge_method": request.GET.get("code_challenge_method", ""),
        "scope": request.GET.get("scope", ""),
    }
    html = f"""<!DOCTYPE html>
<html>
  <body>
    <video id='video' autoplay></video>
    <button id='submit'>Continue</button>
    <script>
      const params = {json.dumps(params)};
      navigator.mediaDevices.getUserMedia({{video: true}}).then(stream => {{
        document.getElementById('video').srcObject = stream;
      }});
      document.getElementById('submit').onclick = async () => {{
        const canvas = document.createElement('canvas');
        const v = document.getElementById('video');
        canvas.width = v.videoWidth; canvas.height = v.videoHeight;
        canvas.getContext('2d').drawImage(v,0,0);
        const img = canvas.toDataURL('image/png');
        const resp = await fetch('authorize/verify', {{
          method: 'POST',
          headers: {{'Content-Type':'application/json'}},
          body: JSON.stringify(Object.assign({{image: img}}, params))
        }});
        const data = await resp.json();
        if (data.redirect) {{ window.location = data.redirect; }}
      }};
    </script>
  </body>
</html>"""
    return HttpResponse(html)

@csrf_exempt
def authorize_verify(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    data = json.loads(request.body.decode())
    client_id = data.get("client_id")
    state = data.get("state")
    redirect_uri = data.get("redirect_uri")
    image_b64 = data.get("image")
    if not image_b64:
        return HttpResponseBadRequest("image required")
    try:
        client = OAuthClient.objects.get(client_id=client_id)
    except OAuthClient.DoesNotExist:
        return HttpResponseBadRequest("invalid client")
    # Decode image and run checks
    raw = base64.b64decode(image_b64.split(",")[-1])
    image = Image.open(io.BytesIO(raw))
    bgr = np.array(image)[:, :, ::-1]
    if not liveness.check(bgr):
        return HttpResponseBadRequest("liveness failed")
    user = User.objects.first()
    gallery = [
        np.frombuffer(fe.vector, dtype=np.float32)
        for fe in user.faceembedding_set.filter(active=True)
    ]
    probe = adapter.embed(bgr)
    idx, score = adapter.match(probe, gallery)
    if idx == -1 or score < 0.7:
        return HttpResponseBadRequest("face not recognized")
    session = AuthSession.objects.create(
        client=client,
        user=user,
        state=state,
        nonce=data.get("nonce", ""),
        code_challenge=data.get("code_challenge", ""),
        code_challenge_method=data.get("code_challenge_method", ""),
        redirect_uri=redirect_uri,
        scope=data.get("scope", ""),
        expires_at=timezone.now() + timezone.timedelta(minutes=10),
        verified_face=True,
        liveness_passed=True,
    )
    code = secrets.token_urlsafe(32)
    AuthorizationCode.objects.create(
        session=session,
        code=code,
        expires_at=timezone.now() + timezone.timedelta(minutes=10),
    )
    return JsonResponse({"redirect": f"{redirect_uri}?code={code}&state={state}"})

@csrf_exempt
def token(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    data = json.loads(request.body.decode())
    code = data.get("code")
    try:
        auth_code = AuthorizationCode.objects.get(code=code, consumed_at__isnull=True)
    except AuthorizationCode.DoesNotExist:
        return HttpResponseBadRequest("invalid code")
    verifier = data.get("code_verifier", "")
    challenge = auth_code.session.code_challenge
    if challenge:
        method = auth_code.session.code_challenge_method or "plain"
        if not verifier:
            return HttpResponseBadRequest("code_verifier required")
        if method == "S256":
            digest = hashlib.sha256(verifier.encode()).digest()
            computed = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
        else:
            computed = verifier
        if computed != challenge:
            return HttpResponseBadRequest("pkce verification failed")
    auth_code.consumed_at = timezone.now()
    auth_code.save()
    user = auth_code.session.user or User.objects.first()
    aud = auth_code.session.client.client_id
    nonce = auth_code.session.nonce
    kid = "dev"
    jwks = json.loads(settings.PUBKEY_JWKS)
    if jwks.get("keys"):
        kid = jwks["keys"][0].get("kid", "dev")
    id_token = tokens.mint_id_token(str(user.id), aud, nonce, int(auth_code.session.expires_at.timestamp()), kid)
    access_token = secrets.token_urlsafe(32)
    return JsonResponse({
        "access_token": access_token,
        "token_type": "Bearer",
        "id_token": id_token,
        "expires_in": 600,
    })

def userinfo(request):
    if not request.META.get("HTTP_AUTHORIZATION"):
        return JsonResponse({"detail": "unauthorized"}, status=401)
    user = User.objects.first()
    return JsonResponse({
        "sub": str(user.id),
        "name": user.display_name,
        "email": user.email,
        "picture": user.avatar_url,
    })
