from rest_framework import serializers

from keypro.models import Assignment, Course, Lesson


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
