from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from payments.models import SubscriptionPlan
from payments.serializers import SubscriptionPlanSerializer


class SubscriptionPlanListView(ListAPIView):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [AllowAny]
