import base64
import io
import json
import os

import numpy as np
from PIL import Image
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .models import User, FaceEmbedding
from .auth import login_required_json
from facekit.adapter import FaceAdapter
from facekit.liveness import LivenessChecker
from facekit.detect import FaceDetector
from facekit.crypto import encrypt, decrypt
import logging
import logging


def _read_image_from_request(request):
    """Extract an image from JSON data URL or multipart file field 'image'.

    Returns a PIL Image in RGB or an HttpResponseBadRequest.
    """
    # Multipart form with file
    if request.FILES.get("image"):
        try:
            return Image.open(request.FILES["image"]).convert("RGB")
        except Exception:
            return HttpResponseBadRequest("invalid image upload")
    # JSON with data URL
    try:
        data = json.loads(request.body.decode() or "{}")
    except Exception:
        data = {}
    image_b64 = data.get("image")
    if image_b64 and isinstance(image_b64, str):
        try:
            raw = base64.b64decode(image_b64.split(",")[-1])
            return Image.open(io.BytesIO(raw)).convert("RGB")
        except Exception:
            return HttpResponseBadRequest("invalid image data")
    return HttpResponseBadRequest("image required")


def _gallery_vectors(adapter: FaceAdapter):
    """Return (embeddings, owners) for all active FaceEmbeddings matching adapter.model_name (decrypted)."""
    embeddings = []
    owners = []
    qs = FaceEmbedding.objects.filter(active=True, model_name=adapter.model_name).select_related("user")
    for fe in qs:
        try:
            plaintext = decrypt(bytes(fe.vector))
            vec = np.frombuffer(plaintext, dtype=np.float32)
            embeddings.append(vec)
            owners.append(fe.user)
        except Exception:
            continue
    return embeddings, owners


@csrf_exempt
def face_login(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    # Single-image JSON or multipart
    img = _read_image_from_request(request)
    if isinstance(img, HttpResponseBadRequest):
        return img
    bgr = np.array(img)[:, :, ::-1]
    # Optional liveness check on single image
    checker = LivenessChecker()
    if not checker.check(bgr):
        return HttpResponseBadRequest("liveness failed")
    # Face detection & crop (required if detector configured)
    detector = FaceDetector()
    crop = detector.detect_and_crop(bgr)
    if detector._fn is not None and crop is None:
        return HttpResponseBadRequest("no face detected")
    face_img = crop if crop is not None else bgr
    adapter = FaceAdapter()
    probe = adapter.embed(face_img).astype(np.float32)
    n = float(np.linalg.norm(probe))
    if n > 0:
        probe /= n
    embeddings, owners = _gallery_vectors(adapter)
    if not embeddings:
        return HttpResponseBadRequest("no enrolled faces")
    idx, score = adapter.match(probe, embeddings)
    try:
        threshold = float(os.getenv("FACE_MATCH_THRESHOLD", "0.7"))
    except ValueError:
        threshold = 0.7
    try:
        margin = float(os.getenv("FACE_MATCH_MARGIN", "0.0"))
    except ValueError:
        margin = 0.0
    # Compute full sims for debug and margin checks
    sims = [float(np.dot(probe, g) / (np.linalg.norm(probe) * np.linalg.norm(g))) for g in embeddings]
    sims_sorted = sorted(sims, reverse=True) if sims else []
    top1 = sims_sorted[0] if sims_sorted else 0.0
    top2 = sims_sorted[1] if len(sims_sorted) > 1 else 0.0
    if margin > 0 and len(embeddings) > 1:
        if (top1 - top2) < margin:
            if os.getenv("FACE_DEBUG", "").lower() == "true":
                logging.info("face_login reject (margin): top1=%.3f top2=%.3f thr=%.3f margin=%.3f", top1, top2, threshold, margin)
            payload = {"detail": "user not found"}
            if os.getenv("FACE_DEBUG", "").lower() == "true":
                payload["debug"] = {"top1": top1, "top2": top2, "threshold": threshold, "margin": margin}
            return JsonResponse(payload, status=404)
    if idx == -1 or score < threshold:
        if os.getenv("FACE_DEBUG", "").lower() == "true":
            logging.info("face_login reject (threshold): top1=%.3f top2=%.3f thr=%.3f margin=%.3f", top1, top2, threshold, margin)
        payload = {"detail": "user not found"}
        if os.getenv("FACE_DEBUG", "").lower() == "true":
            payload["debug"] = {"top1": top1, "top2": top2, "threshold": threshold, "margin": margin}
        return JsonResponse(payload, status=404)
    user = owners[idx]
    login(request, user)
    resp = {
        "authenticated": True,
        "user": {"id": user.id, "email": user.email, "display_name": user.display_name},
        "score": score,
    }
    if os.getenv("FACE_DEBUG", "").lower() == "true":
        resp["debug"] = {"top1": top1, "top2": top2, "threshold": threshold, "margin": margin}
        logging.info("face_login accept: top1=%.3f top2=%.3f thr=%.3f margin=%.3f", top1, top2, threshold, margin)
    return JsonResponse(resp)


@csrf_exempt
def face_signup(request):
    """Create a user and enroll one face embedding in a single call.

    Accepts either multipart form fields or JSON body with keys:
    - email (required)
    - display_name (required)
    - password (optional)
    - image (data URL or multipart file under 'image')
    """
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    # Extract fields from multipart or JSON
    content_type = request.META.get("CONTENT_TYPE", "")
    is_multipart = content_type.startswith("multipart/")
    if is_multipart:
        email = request.POST.get("email", "").strip()
        display_name = request.POST.get("display_name", "").strip()
        password = request.POST.get("password", None)
    else:
        try:
            payload = json.loads(request.body.decode() or "{}")
        except Exception:
            payload = {}
        email = (payload.get("email") or "").strip()
        display_name = (payload.get("display_name") or "").strip()
        password = payload.get("password")

    if not email or not display_name:
        return HttpResponseBadRequest("email and display_name required")
    if User.objects.filter(email=email).exists():
        return HttpResponseBadRequest("email already registered")

    img = _read_image_from_request(request)
    if isinstance(img, HttpResponseBadRequest):
        return img

    user = User.objects.create_user(email=email, password=password, display_name=display_name)
    adapter = FaceAdapter()
    bgr = np.array(img)[:, :, ::-1]
    checker = LivenessChecker()
    if not checker.check(bgr):
        return HttpResponseBadRequest("liveness failed")
    detector = FaceDetector()
    crop = detector.detect_and_crop(bgr)
    if detector._fn is not None and crop is None:
        return HttpResponseBadRequest("no face detected")
    face_img = crop if crop is not None else bgr
    vector_enc = adapter.embed_and_encrypt(face_img)
    FaceEmbedding.objects.create(user=user, model_name=adapter.model_name, vector=vector_enc)
    login(request, user)
    return JsonResponse({
        "created": True,
        "user": {"id": user.id, "email": user.email, "display_name": user.display_name},
    }, status=201)


@csrf_exempt
@login_required_json
def face_enroll(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    img = _read_image_from_request(request)
    if isinstance(img, HttpResponseBadRequest):
        return img
    adapter = FaceAdapter()
    bgr = np.array(img)[:, :, ::-1]
    detector = FaceDetector()
    crop = detector.detect_and_crop(bgr)
    if detector._fn is not None and crop is None:
        return HttpResponseBadRequest("no face detected")
    face_img = crop if crop is not None else bgr
    vector_enc = adapter.embed_and_encrypt(face_img)
    FaceEmbedding.objects.create(user=request.user, model_name=adapter.model_name, vector=vector_enc)
    return JsonResponse({"enrolled": True})


@csrf_exempt
@login_required_json
def face_reenroll(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    img = _read_image_from_request(request)
    if isinstance(img, HttpResponseBadRequest):
        return img
    adapter = FaceAdapter()
    bgr = np.array(img)[:, :, ::-1]
    checker = LivenessChecker()
    if not checker.check(bgr):
        return HttpResponseBadRequest("liveness failed")
    # Deactivate previous embeddings
    FaceEmbedding.objects.filter(user=request.user, active=True).update(active=False)
    vector_enc = adapter.embed_and_encrypt(bgr)
    FaceEmbedding.objects.create(user=request.user, model_name=adapter.model_name, vector=vector_enc)
    return JsonResponse({"reenrolled": True})
