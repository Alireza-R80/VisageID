import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = ["*"]
FACE_DEBUG = os.getenv("FACE_DEBUG", "").lower() == "true"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "accounts",
    "orgs",
    "oauth",
    "facekit",
    "audit",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # Dev CORS (before CSRF)
    "config.dev_cors.DevCorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "audit.middleware.AuditMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_USER_MODEL = "accounts.User"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

OIDC_ISSUER = os.getenv("OIDC_ISSUER", "http://localhost:8000")
PUBKEY_JWKS = os.getenv("PUBKEY_JWKS", '{"keys": []}')
PRIVKEY_PEM = os.getenv("PRIVKEY_PEM", "")
PRIVKEY_PEM_FILE = os.getenv("PRIVKEY_PEM_FILE", "")
if not PRIVKEY_PEM and PRIVKEY_PEM_FILE:
    try:
        PRIVKEY_PEM = Path(PRIVKEY_PEM_FILE).read_text()
    except Exception:
        PRIVKEY_PEM = ""
ACCESS_TOKENS_AS_JWT = os.getenv("ACCESS_TOKENS_AS_JWT", "true").lower() == "true"

# Dev CORS: allow frontend origin during development
_dev_origins_env = os.getenv("DEV_CORS_ORIGINS", "")
DEV_CORS_ORIGINS = [o.strip() for o in _dev_origins_env.split(",") if o.strip()]
if DEBUG and not DEV_CORS_ORIGINS:
    DEV_CORS_ORIGINS = ["http://localhost:3000"]

# Console logging for face debug
if FACE_DEBUG:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
            },
        },
        "formatters": {
            "simple": {
                "format": "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "INFO",
        },
    }
