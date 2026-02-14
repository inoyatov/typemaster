from django.utils import timezone
from rest_framework.permissions import BasePermission

from payments.models import Subscription


class HasLessonAccess(BasePermission):
    message = "Active subscription required to access paid lessons."

    def has_object_permission(self, request, view, obj):
        if obj.is_free:
            return True
        if not request.user.is_authenticated:
            return False
        now = timezone.now()
        return Subscription.objects.filter(
            user=request.user,
            starts_at__lte=now,
            expires_at__gte=now,
        ).exists()
