from django.urls import path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from accounts.views import TelegramWebhookView

from .base import urlpatterns  # noqa

schema_view = get_schema_view(
    openapi.Info(
        title="Academy API",
        default_version="v1",
        description="API used for Online Academy Project",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=False,
    permission_classes=(permissions.IsAdminUser,),
)

urlpatterns += [
    path(
        "api/auth/telegram/webhook/",
        TelegramWebhookView.as_view(),
        name="telegram-webhook",
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "redoc/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),
]
