from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from keypro.models import Course, CourseEnrollment, Lesson
from keypro.permissions import HasLessonAccess
from keypro.serializers import (
    CourseListSerializer,
    EnrollmentSerializer,
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


class EnrollmentListView(ListAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CourseEnrollment.objects.filter(
            user=self.request.user
        ).select_related("course")


class EnrollmentDetailView(RetrieveAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CourseEnrollment.objects.filter(
            user=self.request.user
        ).select_related("course")


class CourseEnrollView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id, is_active=True)
        enrollment, created = CourseEnrollment.objects.get_or_create(
            user=request.user, course=course
        )
        if not created and enrollment.status in (
            CourseEnrollment.CANCELED,
            CourseEnrollment.PAUSED,
        ):
            enrollment.status = CourseEnrollment.ACTIVE
            enrollment.last_activity_at = timezone.now()
            enrollment.save(update_fields=["status", "last_activity_at"])
        serializer = EnrollmentSerializer(enrollment)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class CourseEnrollmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        enrollment = get_object_or_404(
            CourseEnrollment.objects.select_related("course"),
            user=request.user,
            course_id=course_id,
        )
        serializer = EnrollmentSerializer(enrollment)
        return Response(serializer.data)


class EnrollmentCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        enrollment = get_object_or_404(
            CourseEnrollment.objects.select_related("course"),
            pk=pk,
            user=request.user,
        )
        if enrollment.status not in (
            CourseEnrollment.ACTIVE,
            CourseEnrollment.PAUSED,
        ):
            return Response(
                {
                    "detail": f"Cannot cancel enrollment "
                    f"with status '{enrollment.status}'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        enrollment.status = CourseEnrollment.CANCELED
        enrollment.save(update_fields=["status"])
        serializer = EnrollmentSerializer(enrollment)
        return Response(serializer.data)


class EnrollmentResumeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        enrollment = get_object_or_404(
            CourseEnrollment.objects.select_related("course"),
            pk=pk,
            user=request.user,
        )
        if enrollment.status not in (
            CourseEnrollment.CANCELED,
            CourseEnrollment.PAUSED,
        ):
            return Response(
                {
                    "detail": f"Cannot resume enrollment "
                    f"with status '{enrollment.status}'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        enrollment.status = CourseEnrollment.ACTIVE
        enrollment.last_activity_at = timezone.now()
        enrollment.save(update_fields=["status", "last_activity_at"])
        serializer = EnrollmentSerializer(enrollment)
        return Response(serializer.data)
