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

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if not instance.is_free and (
            not request or not request.user.is_authenticated
        ):
            data["text_content"] = None
        return data
