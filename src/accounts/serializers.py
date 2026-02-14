from django.conf import settings
from rest_framework import serializers

from accounts.models import AuthCode


class AuthCodeSerializer(serializers.Serializer):
    auth_code = serializers.CharField()

    def validate_auth_code(self, value):
        if len(value) != settings.OTP_LENGTH:
            raise serializers.ValidationError(
                f"Auth code must be {settings.OTP_LENGTH} digits."
            )

        try:
            auth_code = AuthCode.objects.select_related("user").get(code=value)
        except AuthCode.DoesNotExist:
            raise serializers.ValidationError(
                "Submitted code doesn't exist. "
                "Please obtain a new one by using the Telegram bot."
            ) from None

        if auth_code.is_expired:
            raise serializers.ValidationError(
                "Submitted code has expired. "
                "Please obtain a new one by using the Telegram bot."
            )

        self.auth_code = auth_code
        return value
