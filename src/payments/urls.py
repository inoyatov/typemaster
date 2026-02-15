from django.urls import path

from payments.views import (
    InitiatePaymentView,
    ResendCodeView,
    SubscriptionPlanListView,
    VerifyPaymentView,
)

urlpatterns = [
    path(
        "subscription-plans/",
        SubscriptionPlanListView.as_view(),
        name="subscription-plan-list",
    ),
    path(
        "subscription/pay/initiate/",
        InitiatePaymentView.as_view(),
        name="payment-initiate",
    ),
    path(
        "subscription/pay/verify/",
        VerifyPaymentView.as_view(),
        name="payment-verify",
    ),
    path(
        "subscription/pay/resend-code/",
        ResendCodeView.as_view(),
        name="payment-resend-code",
    ),
]
