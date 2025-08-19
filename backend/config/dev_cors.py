from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.cache import patch_vary_headers


def _parse_origins(val: str):
    return [o.strip() for o in (val or '').split(',') if o.strip()]


class DevCorsMiddleware(MiddlewareMixin):
    """Lightweight CORS for development only.

    Enables credentials for configured origins (e.g., http://localhost:3000).
    Configure via env DEV_CORS_ORIGINS=comma,separated,origins
    """

    def __init__(self, get_response=None):
        super().__init__(get_response)
        from django.conf import settings
        self.allowed = set(getattr(settings, 'DEV_CORS_ORIGINS', []) or [])

    def _origin_allowed(self, request):
        origin = request.META.get('HTTP_ORIGIN')
        return origin if origin and origin in self.allowed else None

    def process_request(self, request):
        origin = self._origin_allowed(request)
        if origin and request.method == 'OPTIONS' and request.META.get('HTTP_ACCESS_CONTROL_REQUEST_METHOD'):
            resp = HttpResponse(status=200)
            self._set_headers(resp, origin)
            return resp
        return None

    def process_response(self, request, response):
        origin = self._origin_allowed(request)
        if origin:
            self._set_headers(response, origin)
            patch_vary_headers(response, ('Origin',))
        return response

    def _set_headers(self, response, origin):
        response['Access-Control-Allow-Origin'] = origin
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken'

