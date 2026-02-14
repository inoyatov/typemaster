import debug_toolbar
from django.urls import include, path
from django.views.generic import TemplateView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from .base import urlpatterns

schema_view = get_schema_view(
    openapi.Info(
        title="Academy API",
        default_version="v1",
        description="API used for Online Academy Project",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns += [
    path("__debug__/", include(debug_toolbar.urls)),
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
    path(
        "auth/password/reset/<str:user>/<str:key>/",
        TemplateView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "auth/registration/account-confirm-email/<str:key>/",
        TemplateView.as_view(),
        name="account_confirm_email",
    ),
]
