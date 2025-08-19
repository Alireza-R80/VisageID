import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from .models import User
from .auth import login_required_json
from .models_email import EmailVerificationToken


@csrf_exempt
@login_required_json
def profile_api(request):
    if request.method == "GET":
        u = request.user
        return JsonResponse({
            "id": u.id,
            "email": u.email,
            "display_name": u.display_name,
            "avatar_url": u.avatar_url,
            "email_verified": getattr(u, "email_verified", False),
        })
    if request.method == "PUT":
        try:
            data = json.loads(request.body.decode() or "{}")
        except Exception:
            data = {}
        u = request.user
        if "display_name" in data:
            u.display_name = data["display_name"]
        if "avatar_url" in data:
            u.avatar_url = data["avatar_url"]
        u.save()
        return JsonResponse({"updated": True})
    if request.method == "DELETE":
        u = request.user
        u.is_active = False
        if not u.deleted_at:
            from django.utils import timezone
            u.deleted_at = timezone.now()
        u.save()
        return JsonResponse({"deleted": True})
    return HttpResponseBadRequest("Unsupported method")


@csrf_exempt
def request_verify_email(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    try:
        data = json.loads(request.body.decode() or "{}")
    except Exception:
        data = {}
    email = (data.get("email") or "").strip()
    if not email:
        return HttpResponseBadRequest("email required")
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return HttpResponseBadRequest("unknown email")
    token = EmailVerificationToken.create_for(user)
    # In real deployment, send token via email. For now, return for testing
    return JsonResponse({"verification_token": token.token})


@csrf_exempt
def verify_email(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    try:
        data = json.loads(request.body.decode() or "{}")
    except Exception:
        data = {}
    token_str = data.get("token")
    if not token_str:
        return HttpResponseBadRequest("token required")
    try:
        tok = EmailVerificationToken.objects.get(token=token_str, consumed_at__isnull=True)
    except EmailVerificationToken.DoesNotExist:
        return HttpResponseBadRequest("invalid token")
    from django.utils import timezone
    if tok.expires_at <= timezone.now():
        return HttpResponseBadRequest("token expired")
    user = tok.user
    user.email_verified = True
    user.save()
    tok.consumed_at = timezone.now()
    tok.save()
    return JsonResponse({"verified": True})


@csrf_exempt
def signup_plain(request):
    """Creates a user without a face image and logs them in.

    Body JSON: { email, display_name, password? }
    """
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    try:
        data = json.loads(request.body.decode() or "{}")
    except Exception:
        data = {}
    email = (data.get("email") or "").strip()
    display_name = (data.get("display_name") or "").strip()
    password = data.get("password")
    if not email or not display_name:
        return HttpResponseBadRequest("email and display_name required")
    if User.objects.filter(email=email).exists():
        return HttpResponseBadRequest("email already registered")
    user = User.objects.create_user(email=email, password=password, display_name=display_name)
    from django.contrib.auth import login
    login(request, user)
    return JsonResponse({"created": True, "user": {"id": user.id, "email": user.email, "display_name": user.display_name}}, status=201)
