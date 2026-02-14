import os

import dj_database_url
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # noqa

###############################################################################
# General
###############################################################################
DEBUG = False
ALLOWED_HOSTS = os.environ.get("ENV_ALLOWED_HOSTS", "*").split(",")
ROOT_URLCONF = "config.urls.staging"
ENVIRONMENT = ENVIRONMENTS.STAGING  # noqa


###############################################################################
# Heroku SSL configuration
# https://help.heroku.com/J2R1S4T8/
###############################################################################
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True


###############################################################################
# Database — parsed from DATABASE_URL provided by Heroku
###############################################################################
MAX_CONN_AGE = 600
DATABASES = {
    "default": dj_database_url.config(
        env="ENV_POSTGRES_DB_URL",
        conn_max_age=int(
            os.environ.get("ENV_POSTGRES_DB_CONN_MAX_AGE", MAX_CONN_AGE),
        ),
        ssl_require=True,
    ),
}


###############################################################################
# Static files — served by WhiteNoise
###############################################################################
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")  # noqa

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MIDDLEWARE.insert(  # noqa
    MIDDLEWARE.index("django.middleware.common.CommonMiddleware"),  # noqa
    "whitenoise.middleware.WhiteNoiseMiddleware",
)


###############################################################################
# CORS
###############################################################################
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.vercel\.app$",
]


###############################################################################
# Sentry
###############################################################################
if os.environ.get("ENV_SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.environ["ENV_SENTRY_DSN"],
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=True,
    )
