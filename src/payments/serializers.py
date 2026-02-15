from rest_framework import serializers

from payments.models import SubscriptionPlan


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ["id", "name", "duration_days", "price"]


class InitiatePaymentSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    card_pan = serializers.RegexField(
        r"^\d{16}$",
        error_messages={"invalid": "Card number must be 16 digits."},
    )
    expiry_month = serializers.IntegerField(min_value=1, max_value=12)
    expiry_year = serializers.IntegerField(min_value=0, max_value=99)

    def validate_plan_id(self, value):
        try:
            return SubscriptionPlan.objects.get(id=value, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError(
                "Subscription plan not found."
            ) from None


class VerifyPaymentSerializer(serializers.Serializer):
    payment_attempt_id = serializers.UUIDField()
    verification_code = serializers.RegexField(
        r"^\d{6}$",
        error_messages={"invalid": "Verification code must be 6 digits."},
    )


class ResendCodeSerializer(serializers.Serializer):
    payment_attempt_id = serializers.UUIDField()
