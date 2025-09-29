"""
Django settings for config project
"""

from pathlib import Path
import os
from datetime import timedelta

from dotenv import load_dotenv
import dj_database_url

# ------------------------------------------------------------------------------
# Paths / .env
# ------------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
# Lee exactamente el .env que está junto a manage.py y permite sobrescribir
load_dotenv(BASE_DIR / ".env", override=True)

# ------------------------------------------------------------------------------
# Seguridad / Debug
# ------------------------------------------------------------------------------
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "dev-only-secret-key-change-me"  # <- cambia en producción
)

# Acepta "1", "true", "True" como True
DEBUG = os.getenv("DEBUG", "0").lower() in ("1", "true", "yes")

ALLOWED_HOSTS = [h for h in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h]

# ------------------------------------------------------------------------------
# Apps
# ------------------------------------------------------------------------------
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Terceros
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "drf_spectacular",
    "corsheaders",

    # Tus apps
    "core",
    "todos",
    "condominio.apps.CondominioConfig",
]

# ------------------------------------------------------------------------------
# REST Framework
# ------------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

# ------------------------------------------------------------------------------
# Middleware
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",          # estáticos en prod
    "corsheaders.middleware.CorsMiddleware",               # CORS antes de Common
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Si estás detrás de proxy (Render/Heroku) y usas HTTPS
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ------------------------------------------------------------------------------
# Base de datos (Neon)
# ------------------------------------------------------------------------------
DATABASES = {
    "default": dj_database_url.parse(
        os.getenv("DATABASE_URL"),
        conn_max_age=600,   # conexiones persistentes
        ssl_require=True,   # SSL obligatorio con Neon
    )
}

# ------------------------------------------------------------------------------
# Internacionalización
# ------------------------------------------------------------------------------
LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "es")
TIME_ZONE = os.getenv("TIME_ZONE", "UTC")  # ej. "America/Lima"
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------------------
# Archivos estáticos y media
# ------------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ------------------------------------------------------------------------------
# CORS / CSRF (ajusta dominios de tu frontend en producción)
# ------------------------------------------------------------------------------
def _split_env(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]

CORS_ALLOWED_ORIGINS = _split_env(
    "CORS_ALLOWED_ORIGINS",
    "http://127.0.0.1:5173,http://localhost:5173"
)
CSRF_TRUSTED_ORIGINS = _split_env(
    "CSRF_TRUSTED_ORIGINS",
    "http://127.0.0.1:5173,http://localhost:5173"
)
CORS_ALLOW_CREDENTIALS = False  # pon True si vas a usar cookies/sesiones

# ------------------------------------------------------------------------------
# Varios
# ------------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Ejemplo de var opcional (si la usas):
MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "")
