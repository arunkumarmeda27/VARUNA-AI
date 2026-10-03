"""
VARUNA-AI: Django Settings Configuration
Owner: Member 5 (Backend + Platform Integration Engineer)
"""

import os
import secrets
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# SECURITY / ENVIRONMENT
# ============================================================

def _env_bool(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


DEBUG = _env_bool("DJANGO_DEBUG", True)
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY must be configured when DJANGO_DEBUG is false."
        )
    SECRET_KEY = secrets.token_urlsafe(50)

allowed_hosts_value = os.getenv(
    "DJANGO_ALLOWED_HOSTS",
    "127.0.0.1,localhost" if DEBUG else "",
)
ALLOWED_HOSTS = [
    host.strip()
    for host in allowed_hosts_value.split(",")
    if host.strip()
]
if not DEBUG and (not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS):
    raise ImproperlyConfigured(
        "Set DJANGO_ALLOWED_HOSTS to explicit production hostnames."
    )


# Production HTTPS settings.
# Keep disabled for local development.
SECURE_SSL_REDIRECT = _env_bool(
    "DJANGO_SECURE_SSL_REDIRECT", not DEBUG
)

SECURE_HSTS_SECONDS = int(
    os.getenv(
        "DJANGO_SECURE_HSTS_SECONDS",
        "0"
    )
)

SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", False
)

SECURE_HSTS_PRELOAD = _env_bool("DJANGO_SECURE_HSTS_PRELOAD", False)

SESSION_COOKIE_SECURE = _env_bool(
    "DJANGO_SESSION_COOKIE_SECURE", not DEBUG
)

CSRF_COOKIE_SECURE = _env_bool(
    "DJANGO_CSRF_COOKIE_SECURE", not DEBUG
)

if not DEBUG:
    if not SECURE_SSL_REDIRECT:
        raise ImproperlyConfigured(
            "DJANGO_SECURE_SSL_REDIRECT must be enabled in production."
        )
    if not SESSION_COOKIE_SECURE or not CSRF_COOKIE_SECURE:
        raise ImproperlyConfigured(
            "Secure session and CSRF cookies are required in production."
        )
    if SECURE_HSTS_SECONDS <= 0:
        raise ImproperlyConfigured(
            "Set DJANGO_SECURE_HSTS_SECONDS to a positive production value."
        )

if os.getenv(
    "DJANGO_TRUST_PROXY_SSL",
    "false"
).lower() in {
    "1",
    "true",
    "yes",
    "on",
}:
    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )


# ============================================================
# APPLICATIONS
# ============================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "backend",
    "dashboard",
    "rest_framework",
    "drf_spectacular",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================================================
# URL CONFIGURATION
# ============================================================

ROOT_URLCONF = "backend.urls"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(
                BASE_DIR,
                "dashboard",
                "templates",
            )
        ],
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


# ============================================================
# WSGI
# ============================================================

WSGI_APPLICATION = "backend.wsgi.application"


# ============================================================
# DATABASE
# ============================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "varuna_db.sqlite3",
    }
}


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME":
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator",
    },
    {
        "NAME":
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator",
    },
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    os.path.join(
        BASE_DIR,
        "dashboard",
        "static",
    )
]


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

API_PREDICT_RATE = os.getenv("DJANGO_API_PREDICT_RATE", "30/m")
API_READ_RATE = os.getenv("DJANGO_API_READ_RATE", "120/m")
API_LOGIN_PAGE_RATE = os.getenv("DJANGO_API_LOGIN_PAGE_RATE", "30/m")

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "backend.api_exceptions.api_exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "VARUNA-AI API",
    "DESCRIPTION": "Forecast inference API.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}