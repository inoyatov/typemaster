import os

from .base import *  # noqa

###################################################################
# General
###################################################################
DEBUG = True
ALLOWED_HOSTS = ["*"]
ROOT_URLCONF = "config.urls.development"
ENVIRONMENT = ENVIRONMENTS.DEVELOPMENT  # noqa


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
            os.environ.get("ENV_POSTGRES_DB_CONN_MAX_AGE", 600),
        ),
    }
}


###################################################################
# Templates
###################################################################
TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG  # noqa


###################################################################
# CORS
###################################################################
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True


###################################################################
# Static and Media assets
###################################################################
MEDIA_ROOT = os.path.join(BASE_DIR, "media")  # noqa
MEDIA_URL = "/media/"

STATIC_URL = "/static/"

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)


###################################################################
# Logging
###################################################################
FORMATTERS = {
    "standard": {
        "format": (
            "%(asctime)s %(levelname)s [%(name)s: %(lineno)s] -- %(message)s"
        )
    }
}

HANDLERS = {
    "console": {
        "level": "DEBUG",
        "class": "logging.StreamHandler",
        "formatter": "standard",
    }
}

LOGGERS = {"": {"handlers": ["console"], "level": "INFO"}}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": FORMATTERS,
    "handlers": HANDLERS,
    "loggers": LOGGERS,
}


###################################################################
# Installed Apps
###################################################################
INSTALLED_APPS += ["debug_toolbar", "drf_yasg"]  # noqa


###################################################################
# Middleware
###################################################################
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa


###################################################################
# Debug Toolbar
###################################################################
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda x: (
        os.environ.get(
            "ENV_DJANGO_TOOLBAR_SHOW_TOOLBAR_CALLBACK", "false"
        ).lower()
        == "true"
    )
}
