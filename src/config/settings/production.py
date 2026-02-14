import os

import dj_database_url
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # noqa

###############################################################################
# General
###############################################################################
ALLOWED_HOSTS = ["*"]
DEBUG = False
ROOT_URLCONF = "config.urls.production"
WHITENOISE_KEEP_ONLY_HASHED_FILES = True
ENVIRONMENT = ENVIRONMENTS.STAGING  # noqa


###############################################################################
# Heroku SSL related configuration to redirect users to https
# - Read more:
# https://help.heroku.com/J2R1S4T8/
# can-heroku-force-an-application-to-use-ssl-tls
###############################################################################
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True


###############################################################################
# Static & Media assets
###############################################################################
MEDIA_ROOT = os.path.join(BASE_DIR, "media")  # noqa
MEDIA_URL = "/media/"

AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
AWS_STORAGE_BUCKET_NAME = os.environ["AWS_STORAGE_BUCKET_NAME"]
AWS_DEFAULT_ACL = "public-read"
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}

# S3 Static Settings
STATIC_LOCATION = "static"
STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{STATIC_LOCATION}/"
STATICFILES_STORAGE = "common.storage_backends.StaticStorage"

# S3 Public Media Settings
PUBLIC_MEDIA_LOCATION = "media"
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{PUBLIC_MEDIA_LOCATION}/"
DEFAULT_FILE_STORAGE = "common.storage_backends.PublicMediaStorage"

# S3 Private Media Settings
PRIVATE_MEDIA_LOCATION = "private"
PRIVATE_FILE_STORAGE = "common.storage_backends.PrivateMediaStorage"


###############################################################################
# Database
###############################################################################
MAX_CONN_AGE = 600
DATABASES = {
    "default": dj_database_url.config(  # noqa
        env="ENV_POSTGRES_DB_URL",
        conn_max_age=int(
            os.environ.get("ENV_POSTGRES_DB_CONN_MAX_AGE", MAX_CONN_AGE),
        ),
        ssl_require=True,
    ),
}


###############################################################################
# Installed Apps
###############################################################################
THIRD_PARTY_APPS += [  # noqa
    "storages",
]

INSTALLED_APPS = BASE_APPS + THIRD_PARTY_APPS + LOCAL_APPS  # noqa


###############################################################################
# CORS
###############################################################################
CORS_ALLOWED_ORIGINS = [
    "https://skillup.uz",
]


###############################################################################
# SENTRY
###############################################################################
sentry_sdk.init(
    dsn=os.environ.get("ENV_SENTRY_DSN"),
    integrations=[DjangoIntegration()],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=1.0,
    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True,
)


###############################################################################
# REST Framework Configuration
###############################################################################
REST_AUTH.update(  # noqa
    {
        "PASSWORD_RESET_SERIALIZER": "accounts.serializers.CustomPasswordResetSerializer"
    }
)

###############################################################################
# CORS
###############################################################################
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://\w+\.skillup\.uz$",
]
