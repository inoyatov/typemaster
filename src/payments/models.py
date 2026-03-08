import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    duration_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "subscription_plan"
        ordering = ("duration_days",)

    def __str__(self):
        return f"{self.name} ({self.duration_days} days)"


class Subscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )
    starts_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "subscription"
        ordering = ("-created_at",)
        indexes = [
            models.Index(
                fields=["user", "expires_at"],
                name="subscription_user_expires",
            ),
        ]

    def __str__(self):
        return f"{self.user} — {self.plan.name}"

    @property
    def is_active(self):
        now = timezone.now()
        return self.starts_at <= now <= self.expires_at


class PaymentAttempt(models.Model):
    INITIATED = "initiated"
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

    STATUS_CHOICES = [
        (INITIATED, "Initiated"),
        (PENDING, "Pending"),
        (SUCCESS, "Success"),
        (FAILED, "Failed"),
    ]

    guid = models.UUIDField(default=uuid.uuid4, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payment_attempts",
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=INITIATED
    )
    verification_id = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payment_attempt"
        ordering = ("-created_at",)

    def __str__(self):
        return f"Payment {self.guid} — {self.status}"
