from django.urls import path

from payments.views import SubscriptionPlanListView

urlpatterns = [
    path(
        "subscription-plans/",
        SubscriptionPlanListView.as_view(),
        name="subscription-plan-list",
    ),
]
