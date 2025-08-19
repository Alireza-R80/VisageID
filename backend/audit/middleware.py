from .models import AuditLog
from django.utils.deprecation import MiddlewareMixin


SENSITIVE_PATHS = (
    '/oauth/authorize', '/oauth/authorize/verify', '/oauth/token', '/oauth/userinfo',
    '/oauth/revoke', '/oauth/introspect', '/oauth/logout',
    '/account/face/login', '/account/face/signup', '/account/face/enroll', '/account/face/reenroll'
)


class AuditMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        try:
            path = request.path
            if any(path.startswith(p) for p in SENSITIVE_PATHS):
                event = f"{request.method} {path} {response.status_code}"
                ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
                ua = request.META.get('HTTP_USER_AGENT', '')[:255]
                org = None
                client = None
                user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
                AuditLog.objects.create(event=event, ip=ip, ua=ua, org=org, client=client, user=user, meta_json={})
        except Exception:
            pass
        return response

