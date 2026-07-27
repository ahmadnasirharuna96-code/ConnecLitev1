"""
Django settings for ConnectLite.

All secrets and environment-specific values come from environment
variables (see /.env.example at the repo root). Nothing sensitive is
hardcoded here.
"""
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    AT_DEMO_MODE=(bool, True),
)
# Look for backend/.env (copied from the root .env.example)
environ.Env.read_env(BASE_DIR / ".env")

# ------------------------------------------------------------------
# Core
# ------------------------------------------------------------------
SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env("DJANGO_DEBUG")
ENVIRONMENT = env("DJANGO_ENVIRONMENT", default="development")

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Render (and most PaaS providers) terminate TLS at a proxy and forward
# plain HTTP internally with X-Forwarded-Proto — without this, Django's
# request.is_secure() incorrectly returns False, which can break CSRF
# validation (e.g. /admin/ login) due to an http/https scheme mismatch.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[f"https://{host}" for host in ALLOWED_HOSTS if host not in ("localhost", "127.0.0.1")],
)

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# ------------------------------------------------------------------
# Applications
# ------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.profiles",
    "apps.matching",
    "apps.communities",
    "apps.messaging",
    "apps.notifications",
    "apps.airtime",
    "apps.ussd",
    "apps.voice",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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
ASGI_APPLICATION = "config.asgi.application"

# ------------------------------------------------------------------
# Database (PostgreSQL)
# ------------------------------------------------------------------
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"postgres://{env('DB_USER', default='connectlite')}:"
        f"{env('DB_PASSWORD', default='connectlite')}@"
        f"{env('DB_HOST', default='localhost')}:"
        f"{env('DB_PORT', default='5432')}/"
        f"{env('DB_NAME', default='connectlite')}",
    )
}

# ------------------------------------------------------------------
# Custom User model
# ------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------------------------------------------
# Internationalization
# ------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lagos"
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------
# Static / media
# ------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ------------------------------------------------------------------
# DRF
# ------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "20/min",
        "user": "120/min",
        "otp": "5/min",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "ConnectLite API",
    "DESCRIPTION": "Offline-first social & dating platform API",
    "VERSION": "1.0.0",
}

# ------------------------------------------------------------------
# JWT
# ------------------------------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=30)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=7)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# ------------------------------------------------------------------
# CORS
# ------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:5173"])
CORS_ALLOW_CREDENTIALS = True

# ------------------------------------------------------------------
# Africa's Talking
# ------------------------------------------------------------------
AFRICASTALKING = {
    "USERNAME": env("AT_USERNAME", default="sandbox"),
    "API_KEY": env("AT_API_KEY", default=""),
    "ENVIRONMENT": env("AT_ENVIRONMENT", default="sandbox"),
    "SENDER_ID": env("AT_SENDER_ID", default=""),
    "DEMO_MODE": env("AT_DEMO_MODE"),
}

# ------------------------------------------------------------------
# OTP
# ------------------------------------------------------------------
OTP_SETTINGS = {
    "LENGTH": env.int("OTP_LENGTH", default=6),
    "EXPIRY_MINUTES": env.int("OTP_EXPIRY_MINUTES", default=5),
    "MAX_ATTEMPTS": env.int("OTP_MAX_ATTEMPTS", default=3),
    "RESEND_COOLDOWN_SECONDS": env.int("OTP_RESEND_COOLDOWN_SECONDS", default=60),
}

# ------------------------------------------------------------------
# Matching engine (see apps/matching/scoring.py)
# ------------------------------------------------------------------
MATCHING_WEIGHTS = {
    "location": env.float("MATCHING_WEIGHT_LOCATION", default=0.30),
    "interests": env.float("MATCHING_WEIGHT_INTERESTS", default=0.35),
    "age": env.float("MATCHING_WEIGHT_AGE", default=0.20),
    "community": env.float("MATCHING_WEIGHT_COMMUNITY", default=0.15),
}
MATCHING_MAX_AGE_DIFF = env.int("MATCHING_MAX_AGE_DIFF", default=15)

# ------------------------------------------------------------------
# Airtime (see apps/airtime/services.py)
# ------------------------------------------------------------------
AIRTIME_SETTINGS = {
    "MIN_AMOUNT": env.float("AIRTIME_MIN_AMOUNT", default=50.0),
    "MAX_AMOUNT": env.float("AIRTIME_MAX_AMOUNT", default=5000.0),
    "CURRENCY": env.str("AIRTIME_CURRENCY", default="NGN"),
    "REFERRAL_REWARD_AMOUNT": env.float("AIRTIME_REFERRAL_REWARD", default=100.0),
}

# ------------------------------------------------------------------
# Logging — never let OTPs/secrets leak into logs
# ------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "[{asctime}] {levelname} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "connectlite": {"handlers": ["console"], "level": "DEBUG" if DEBUG else "INFO", "propagate": False},
    },
}
