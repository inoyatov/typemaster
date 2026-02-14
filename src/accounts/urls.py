from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import TokenObtainView

urlpatterns = [
    path("token/", TokenObtainView.as_view(), name="token-obtain"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
]
