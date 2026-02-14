from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import (
    MyEnrolledCoursesView,
    MyProfileView,
    MySubscriptionView,
    TokenObtainView,
)

urlpatterns = [
    path("token/", TokenObtainView.as_view(), name="token-obtain"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("my/profile/", MyProfileView.as_view(), name="my-profile"),
    path(
        "my/subscription/",
        MySubscriptionView.as_view(),
        name="my-subscription",
    ),
    path(
        "my/enrolled-courses/",
        MyEnrolledCoursesView.as_view(),
        name="my-enrolled-courses",
    ),
]
