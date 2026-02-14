import os
from datetime import timedelta
from enum import Enum
from pathlib import Path

###############################################################################
# General
###############################################################################
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SECRET_KEY = os.environ["ENV_DJANGO_SECRET_KEY"]
DEBUG = False
ROOT_URLCONF = "config.urls.production"
WSGI_APPLICATION = "config.wsgi.application"
AUTH_USER_MODEL = "accounts.User"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DEFAULT_COURSE_PATH = "courses"
DEFAULT_AUTHOR_AVATAR_PATH = "authors"
DOMAIN_NAME = "skillup.uz"


class ENVIRONMENTS(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    STAGING = "staging"
    TEST = "test"


ENVIRONMENT = ENVIRONMENTS.PRODUCTION


###############################################################################
# CORS
###############################################################################
CORS_ALLOW_HEADERS = (
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-request-with",
    "Cache-Control",
    "http_x_app_version",
)


###############################################################################
# Installed Apps
###############################################################################
BASE_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.postgres",
]

THIRD_PARTY_APPS = [
    "django_extensions",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_yasg",
]

LOCAL_APPS = ["accounts", "payments", "keypro"]

INSTALLED_APPS = BASE_APPS + THIRD_PARTY_APPS + LOCAL_APPS


###############################################################################
# Middleware
###############################################################################
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


###############################################################################
# Templates
###############################################################################
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR / "templates")],
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


###############################################################################
# Authentication
###############################################################################
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation.NumericPasswordValidator"
        ),
    },
]


###############################################################################
# REST Framework Configuration
###############################################################################
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}

REST_AUTH = {
    "USE_JWT": True,
    "JWT_AUTH_HTTPONLY": False,
    "TOKEN_MODEL": None,
    "LOGOUT_ON_PASSWORD_CHANGE": True,
    "REGISTER_SERIALIZER": "accounts.serializers.CustomRegisterSerializer",
    "USER_DETAILS_SERIALIZER": "accounts.serializers.UserDetailsSerializer",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}


###############################################################################
# ALLAUTH Configuration
###############################################################################
SITE_ID = 1
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_LOGOUT_ON_GET = False
OLD_PASSWORD_FIELD_ENABLED = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"


###############################################################################
# Internationalization
###############################################################################
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


###############################################################################
# Django Extensions Configuration
###############################################################################
SHELL_PLUS = "ipython"
SHELL_PLUS_PRINT_SQL = True


###############################################################################
# Telegram Bot & OTP Configuration
###############################################################################
TELEGRAM_BOT_TOKEN = os.environ.get("ENV_TELEGRAM_BOT_TOKEN", "")
TELEGRAM_WEBHOOK_URL = os.environ.get("ENV_TELEGRAM_WEBHOOK_URL", "")
TELEGRAM_WEBHOOK_SECRET = os.environ.get("ENV_TELEGRAM_WEBHOOK_SECRET", "")
OTP_LENGTH = int(os.environ.get("ENV_OTP_LENGTH", 12))
OTP_EXPIRY_MINUTES = 1
