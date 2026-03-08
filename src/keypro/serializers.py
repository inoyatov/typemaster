from rest_framework import serializers

from keypro.models import (
    Assignment,
    CompletedAssignment,
    Course,
    CourseEnrollment,
    Lesson,
)


class CourseListSerializer(serializers.ModelSerializer):
    total_lessons = serializers.IntegerField(read_only=True)

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
        ]


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
    progress_percent = serializers.SerializerMethodField()
    current_lesson_id = serializers.SerializerMethodField()
    started_at = serializers.DateTimeField(source="enrolled_at", read_only=True)

    class Meta:
        model = CourseEnrollment
        fields = [
            "id",
            "course",
            "status",
            "progress_percent",
            "current_lesson_id",
            "started_at",
            "completed_at",
            "last_activity_at",
        ]
        read_only_fields = fields

    def get_progress_percent(self, obj):
        total = Assignment.objects.filter(
            lesson__course=obj.course, is_active=True
        ).count()
        if total == 0:
            return 0.0
        completed = (
            CompletedAssignment.objects.filter(
                user=obj.user,
                assignment__lesson__course=obj.course,
            )
            .values("assignment")
            .distinct()
            .count()
        )
        return round((completed / total) * 100, 1)

    def get_current_lesson_id(self, obj):
        completed_ids = set(
            CompletedAssignment.objects.filter(
                user=obj.user,
                assignment__lesson__course=obj.course,
            ).values_list("assignment_id", flat=True)
        )
        lessons = Lesson.objects.filter(
            course=obj.course, is_active=True
        ).prefetch_related("assignments")
        for lesson in lessons:
            active_assignments = [
                a for a in lesson.assignments.all() if a.is_active
            ]
            if any(a.id not in completed_ids for a in active_assignments):
                return lesson.id
        return None
