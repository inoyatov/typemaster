from django.urls import path

from accounts.views import TelegramWebhookView

from .base import urlpatterns  # noqa

urlpatterns += [
    path(
        "api/auth/telegram/webhook/",
        TelegramWebhookView.as_view(),
        name="telegram-webhook",
    ),
]
