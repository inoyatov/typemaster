import os

from .base import *  # noqa

###################################################################
# General
###################################################################
DEBUG = False
ALLOWED_HOSTS = ["*"]
ROOT_URLCONF = "config.urls.test"
ENVIRONMENT = ENVIRONMENTS.TEST  # noqa


###############################################################################
# Database
###############################################################################
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.environ["ENV_POSTGRES_DB_HOST"],
        "PORT": os.environ["ENV_POSTGRES_DB_PORT"],
        "NAME": os.environ["ENV_POSTGRES_DB_NAME"],
        "USER": os.environ["ENV_POSTGRES_DB_USER"],
        "PASSWORD": os.environ["ENV_POSTGRES_DB_PASSWORD"],
        "CONN_MAX_AGE": int(
            os.environ.get("ENV_POSTGRES_DB_CONN_MAX_AGE", 0),
        ),
    }
}
