from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny

from keypro.models import Course, Lesson
from keypro.permissions import HasLessonAccess
from keypro.serializers import (
    CourseListSerializer,
    LessonDetailSerializer,
    LessonListSerializer,
)


class CourseListView(ListAPIView):
    queryset = Course.objects.filter(is_active=True)
    serializer_class = CourseListSerializer
    permission_classes = [AllowAny]


class LessonListView(ListAPIView):
    serializer_class = LessonListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Lesson.objects.none()
        return Lesson.objects.filter(
            course__slug=self.kwargs["course_slug"],
            is_active=True,
        )


class LessonDetailView(RetrieveAPIView):
    serializer_class = LessonDetailSerializer
    permission_classes = [AllowAny, HasLessonAccess]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Lesson.objects.none()
        return Lesson.objects.filter(
            course__slug=self.kwargs["course_slug"],
            is_active=True,
        )
