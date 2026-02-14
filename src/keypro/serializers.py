from rest_framework import serializers

from keypro.models import Course, Lesson


class CourseListSerializer(serializers.ModelSerializer):
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


class LessonDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            "id",
            "course",
            "title",
            "description",
            "order",
            "text_content",
            "is_free",
            "is_active",
            "created_at",
        ]
