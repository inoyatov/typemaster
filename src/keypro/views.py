from django.db.models import Count, Q
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication

from keypro.models import Course, Lesson
from keypro.permissions import HasLessonAccess
from keypro.serializers import (
    CourseListSerializer,
    LessonDetailSerializer,
    LessonListSerializer,
)


class CourseListView(ListAPIView):
    queryset = Course.objects.filter(is_active=True).annotate(
        total_lessons=Count("lessons", filter=Q(lessons__is_active=True))
    )
    serializer_class = CourseListSerializer
    authentication_classes = []
    permission_classes = [AllowAny]


class LessonListView(ListAPIView):
    serializer_class = LessonListSerializer
    authentication_classes = []
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
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny, HasLessonAccess]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Lesson.objects.none()
        return Lesson.objects.filter(
            course__slug=self.kwargs["course_slug"],
            is_active=True,
        ).prefetch_related("assignments")
