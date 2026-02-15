from django.conf import settings
from rest_framework import serializers

from accounts.models import AuthCode, User
from keypro.models import CompletedLesson, CourseEnrollment
from payments.models import Subscription


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
            auth_code.delete()
            raise serializers.ValidationError(
                "Submitted code has expired. "
                "Please obtain a new one by using the Telegram bot."
            )

        self.auth_code = auth_code
        return value


class MyProfileSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "nickname",
            "display_name",
        ]
        read_only_fields = ["email", "phone_number"]


class MySubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Subscription
        fields = ["plan_name", "starts_at", "expires_at", "is_active"]


class MyEnrolledCourseSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)
    course_slug = serializers.CharField(source="course.slug", read_only=True)
    total_lessons = serializers.SerializerMethodField()
    completed_lessons = serializers.SerializerMethodField()

    class Meta:
        model = CourseEnrollment
        fields = [
            "id",
            "course_title",
            "course_slug",
            "total_lessons",
            "completed_lessons",
            "enrolled_at",
        ]

    def get_total_lessons(self, obj):
        return obj.course.lessons.filter(is_active=True).count()

    def get_completed_lessons(self, obj):
        user = self.context["request"].user
        return (
            CompletedLesson.objects.filter(
                user=user,
                lesson__course=obj.course,
            )
            .values("lesson")
            .distinct()
            .count()
        )
