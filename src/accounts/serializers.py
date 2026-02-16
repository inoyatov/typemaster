from django.conf import settings
from rest_framework import serializers

from accounts.models import AuthCode, User
from keypro.models import Assignment, CompletedAssignment, CourseEnrollment
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
    total_assignments = serializers.SerializerMethodField()
    completed_assignments = serializers.SerializerMethodField()

    class Meta:
        model = CourseEnrollment
        fields = [
            "id",
            "course_title",
            "course_slug",
            "total_assignments",
            "completed_assignments",
            "enrolled_at",
        ]

    def get_total_assignments(self, obj):
        return Assignment.objects.filter(
            lesson__course=obj.course, is_active=True
        ).count()

    def get_completed_assignments(self, obj):
        user = self.context["request"].user
        return (
            CompletedAssignment.objects.filter(
                user=user,
                assignment__lesson__course=obj.course,
            )
            .values("assignment")
            .distinct()
            .count()
        )
