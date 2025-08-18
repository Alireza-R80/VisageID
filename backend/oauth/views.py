import json
import secrets
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
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
    return JsonResponse({"detail": "use frontend"})

@csrf_exempt
def authorize_verify(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")
    data = json.loads(request.body.decode())
    client_id = data.get("client_id")
    state = data.get("state")
    redirect_uri = data.get("redirect_uri")
    try:
        client = OAuthClient.objects.get(client_id=client_id)
    except OAuthClient.DoesNotExist:
        return HttpResponseBadRequest("invalid client")
    session = AuthSession.objects.create(
        client=client,
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
