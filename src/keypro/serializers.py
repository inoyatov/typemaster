from rest_framework import serializers

from keypro.models import (
    Assignment,
    CompletedAssignment,
    Course,
    CourseEnrollment,
    Lesson,
)
from keypro.services import (
    get_completed_lessons_count,
    get_current_lesson_id,
)


class CourseListSerializer(serializers.ModelSerializer):
    total_lessons = serializers.IntegerField(read_only=True)
    is_enrolled = serializers.BooleanField(read_only=True, default=False)
    completed_lessons = serializers.IntegerField(read_only=True, default=0)
    progress_percent = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "cover_image",
            "author",
            "is_active",
            "order",
            "created_at",
            "total_lessons",
            "is_enrolled",
            "completed_lessons",
            "progress_percent",
        ]

    def get_progress_percent(self, obj):
        total = getattr(obj, "total_assignments", 0)
        if total == 0:
            return 0.0
        completed = getattr(obj, "completed_assignments", 0)
        return round((completed / total) * 100, 1)


class LessonListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "description",
            "order",
            "is_free",
            "is_active",
            "created_at",
        ]


class AssignmentEmbeddedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = [
            "id",
            "title",
            "description",
            "order",
            "text_content",
            "is_active",
            "created_at",
        ]


class LessonDetailSerializer(serializers.ModelSerializer):
    assignments = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            "id",
            "course",
            "title",
            "description",
            "order",
            "is_free",
            "is_active",
            "created_at",
            "assignments",
        ]

    def get_assignments(self, obj):
        active_assignments = obj.assignments.filter(is_active=True)
        return AssignmentEmbeddedSerializer(active_assignments, many=True).data


class EnrollmentCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "slug", "title"]


class EnrollmentSerializer(serializers.ModelSerializer):
    course = EnrollmentCourseSerializer(read_only=True)
    started_at = serializers.DateTimeField(source="enrolled_at", read_only=True)
    total_assignments = serializers.IntegerField(read_only=True)
    completed_assignments = serializers.IntegerField(read_only=True)
    total_lessons = serializers.IntegerField(read_only=True)
    progress_percent = serializers.SerializerMethodField()
    current_lesson_id = serializers.SerializerMethodField()
    completed_lessons = serializers.SerializerMethodField()

    class Meta:
        model = CourseEnrollment
        fields = [
            "id",
            "course",
            "status",
            "progress_percent",
            "current_lesson_id",
            "completed_assignments",
            "total_assignments",
            "completed_lessons",
            "total_lessons",
            "started_at",
            "completed_at",
            "last_activity_at",
        ]
        read_only_fields = fields

    def get_progress_percent(self, obj):
        total = getattr(obj, "total_assignments", 0)
        if total == 0:
            return 0.0
        completed = getattr(obj, "completed_assignments", 0)
        return round((completed / total) * 100, 1)

    def get_current_lesson_id(self, obj):
        return get_current_lesson_id(obj.user, obj.course)

    def get_completed_lessons(self, obj):
        return get_completed_lessons_count(obj.user, obj.course)


class AssignmentCompletionInputSerializer(serializers.Serializer):
    action_type = serializers.ChoiceField(
        choices=CompletedAssignment.ActionType.choices,
    )
    average_speed = serializers.IntegerField(
        min_value=1,
    )
    mistakes_count = serializers.IntegerField(
        min_value=0,
    )


class AssignmentCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompletedAssignment
        fields = [
            "id",
            "action_type",
            "average_speed",
            "mistakes_count",
            "completed_at",
        ]
        read_only_fields = fields


class LessonProgressSerializer(serializers.Serializer):
    lesson_id = serializers.IntegerField()
    status = serializers.CharField()
    completed_assignments = serializers.IntegerField()
    total_assignments = serializers.IntegerField()
    progress_percent = serializers.FloatField()
    completed_at = serializers.DateTimeField(allow_null=True)
