from functools import wraps
from django.http import JsonResponse


def login_required_json(view_func):
    """Require an authenticated user; else return 401 JSON instead of redirecting.

    Use for API endpoints where a browser redirect to a login page is not desired.
    """

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return JsonResponse({"detail": "unauthorized"}, status=401)
        return view_func(request, *args, **kwargs)

    return _wrapped

