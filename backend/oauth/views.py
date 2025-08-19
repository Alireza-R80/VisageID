import base64
import hashlib
import io
import json
import secrets

import numpy as np
from PIL import Image
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse, HttpResponseRedirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout as dj_logout
import os
import logging

from .models import AuthSession, AuthorizationCode, Token
from orgs.models import OAuthClient
from accounts.models import User
from facekit.adapter import FaceAdapter
from facekit.liveness import LivenessChecker
from facekit.detect import FaceDetector
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
    content_type = request.META.get("CONTENT_TYPE", "")
    if content_type.startswith("application/json"):
        try:
            data = json.loads(request.body.decode() or "{}")
        except Exception:
            data = {}
    else:
        data = request.POST.dict()
    client_id = data.get("client_id")
    state = data.get("state")
    redirect_uri = data.get("redirect_uri")
    image_b64 = data.get("image")
    if not image_b64:
        if os.getenv("FACE_DEBUG", "").lower() == "true":
            logging.warning("authorize_verify missing payload: ct=%s, has_image=%s", content_type, bool(image_b64))
        return HttpResponseBadRequest("image required")
    try:
        client = OAuthClient.objects.get(client_id=client_id)
    except OAuthClient.DoesNotExist:
        return HttpResponseBadRequest("invalid client")
    # Validate redirect_uri against registered URIs
    if redirect_uri not in (client.redirect_uris or []):
        return HttpResponseBadRequest("invalid redirect_uri")
    # Decode image(s) and run checks
    def to_bgr(data_url):
        raw = base64.b64decode(data_url.split(",")[-1])
        image = Image.open(io.BytesIO(raw))
        return np.array(image)[:, :, ::-1]

    try:
        bgr = to_bgr(image_b64)
    except Exception:
        return HttpResponseBadRequest("invalid image data")

    if not liveness.check(bgr):
        return HttpResponseBadRequest("liveness failed")
    # Build gallery over all active embeddings for current adapter.model_name and keep mapping to user
    embeddings = []
    owners = []
    from accounts.models import FaceEmbedding as FE
    from facekit.crypto import decrypt
    for fe in FE.objects.filter(active=True, model_name=adapter.model_name).select_related("user"):
        try:
            plaintext = decrypt(bytes(fe.vector))
            vec = np.frombuffer(plaintext, dtype=np.float32)
            embeddings.append(vec)
            owners.append(fe.user)
        except Exception:
            continue
    # Detect/crop single frame if detector configured
    detector = FaceDetector()
    crop = detector.detect_and_crop(bgr)
    if detector._fn is not None and crop is None:
        return HttpResponseBadRequest("no face detected")
    face_img = crop if crop is not None else bgr
    probe = adapter.embed(face_img).astype(np.float32)
    n = float(np.linalg.norm(probe))
    if n > 0:
        probe /= n
    idx, score = adapter.match(probe, embeddings)
    import os
    try:
        threshold = float(os.getenv("FACE_MATCH_THRESHOLD", "0.7"))
    except ValueError:
        threshold = 0.7
    try:
        margin = float(os.getenv("FACE_MATCH_MARGIN", "0.0"))
    except ValueError:
        margin = 0.0
    # Optional margin: top-1 must exceed top-2 by margin; add debug logging
    sims = [float(np.dot(probe, g) / (np.linalg.norm(probe) * np.linalg.norm(g))) for g in embeddings]
    sims_sorted = sorted(sims, reverse=True) if sims else []
    top1 = sims_sorted[0] if sims_sorted else 0.0
    top2 = sims_sorted[1] if len(sims_sorted) > 1 else 0.0
    if margin > 0 and len(embeddings) > 1:
        if (top1 - top2) < margin:
            if os.getenv("FACE_DEBUG", "").lower() == "true":
                logging.info("authorize_verify reject (margin): top1=%.3f top2=%.3f thr=%.3f margin=%.3f", top1, top2, threshold, margin)
            return HttpResponseBadRequest("face not recognized")
    if idx == -1 or score < threshold:
        if os.getenv("FACE_DEBUG", "").lower() == "true":
            logging.info("authorize_verify reject (threshold): top1=%.3f top2=%.3f thr=%.3f margin=%.3f", top1, top2, threshold, margin)
        return HttpResponseBadRequest("face not recognized")
    matched_user = owners[idx]
    session = AuthSession.objects.create(
        client=client,
        user=matched_user,
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
    if os.getenv("FACE_DEBUG", "").lower() == "true":
        logging.info("authorize_verify accept: top1=%.3f top2=%.3f thr=%.3f margin=%.3f", top1, top2, threshold, margin)
    return HttpResponseRedirect(f"{redirect_uri}?code={code}&state={state}")

@csrf_exempt
def token(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    # Accept JSON or form-encoded
    if request.META.get("CONTENT_TYPE", "").startswith("application/json"):
        data = json.loads(request.body.decode() or "{}")
    else:
        data = request.POST
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
    # Enforce client authentication and PKCE as per client config
    client = auth_code.session.client
    # Client auth: from Basic header or body
    client_id = None
    client_secret = None
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if auth_header.startswith("Basic "):
        try:
            decoded = base64.b64decode(auth_header.split()[1]).decode()
            client_id, client_secret = decoded.split(":", 1)
        except Exception:
            return HttpResponseBadRequest("invalid client auth header")
    client_id = client_id or data.get("client_id")
    client_secret = client_secret or data.get("client_secret")
    if client.is_confidential:
        import hashlib
        if client_id != client.client_id or not client_secret:
            return HttpResponseBadRequest("invalid client")
        secret_hash = hashlib.sha256(client_secret.encode()).hexdigest()
        if secret_hash != client.client_secret_hash:
            return HttpResponseBadRequest("invalid client secret")
    # PKCE enforcement per client flag
    if client.pkce_enforced and not verifier:
        return HttpResponseBadRequest("code_verifier required")

    auth_code.consumed_at = timezone.now()
    auth_code.save()
    user = auth_code.session.user or User.objects.first()
    aud = client.client_id
    nonce = auth_code.session.nonce
    kid = "dev"
    jwks = json.loads(settings.PUBKEY_JWKS)
    if jwks.get("keys"):
        kid = jwks["keys"][0].get("kid", "dev")
    import time as _time
    id_token = tokens.mint_id_token(
        str(user.id), aud, nonce, int(_time.time()), kid
    )
    access_token = tokens.mint_access_token(
        user, client, auth_code.session.scope
    )
    refresh_token = tokens.mint_refresh_token(
        user, auth_code.session.client, auth_code.session.scope
    )
    return JsonResponse(
        {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "id_token": id_token,
            "expires_in": 600,
        }
    )

def userinfo(request):
    auth = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth.startswith("Bearer "):
        return JsonResponse({"detail": "unauthorized"}, status=401)
    token_str = auth.split()[1]
    tok = tokens.verify_access_token(token_str)
    if not tok:
        return JsonResponse({"detail": "unauthorized"}, status=401)
    user = tok.user
    return JsonResponse(
        {
            "sub": str(user.id),
            "name": user.display_name,
            "email": user.email,
            "picture": user.avatar_url,
            "email_verified": getattr(user, "email_verified", False),
        }
    )


@csrf_exempt
def revoke(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    data = json.loads(request.body.decode())
    token_str = data.get("token")
    try:
        tok = Token.objects.get(jti=token_str)
        tok.revoked_at = timezone.now()
        tok.save()
    except Token.DoesNotExist:
        pass
    return JsonResponse({"revoked": True})


@csrf_exempt
def introspect(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    data = json.loads(request.body.decode())
    token_str = data.get("token")
    try:
        tok = Token.objects.get(jti=token_str)
    except Token.DoesNotExist:
        return JsonResponse({"active": False})
    if tok.revoked_at or tok.expires_at <= timezone.now():
        return JsonResponse({"active": False})
    return JsonResponse(
        {
            "active": True,
            "scope": tok.scope,
            "client_id": tok.client.client_id,
            "token_type": tok.type,
            "exp": int(tok.expires_at.timestamp()),
            "iat": int(tok.issued_at.timestamp()),
            "sub": str(tok.user.id),
        }
    )


def logout_view(request):
    """Logs out local session and optionally redirects to a registered post-logout URI.

    Accepts optional query params: client_id, post_logout_redirect_uri, state.
    """
    client_id = request.GET.get("client_id")
    post_logout_redirect_uri = request.GET.get("post_logout_redirect_uri")
    state = request.GET.get("state", "")
    client = None
    if client_id:
        try:
            client = OAuthClient.objects.get(client_id=client_id)
        except OAuthClient.DoesNotExist:
            client = None
    dj_logout(request)
    if client and post_logout_redirect_uri and post_logout_redirect_uri in (client.post_logout_redirect_uris or []):
        uri = f"{post_logout_redirect_uri}?state={state}" if state else post_logout_redirect_uri
        return HttpResponseRedirect(uri)
    return JsonResponse({"logged_out": True})
