from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from keypro.models import (
    Assignment,
    CompletedAssignment,
    Course,
    CourseEnrollment,
    Lesson,
)
from keypro.permissions import HasLessonAccess
from keypro.serializers import (
    AssignmentCompletionInputSerializer,
    AssignmentCompletionSerializer,
    CourseListSerializer,
    EnrollmentSerializer,
    LessonDetailSerializer,
    LessonListSerializer,
    LessonProgressSerializer,
)
from keypro.services import (
    complete_assignment,
    get_course_list_queryset,
    get_enrollment_queryset_with_progress,
    get_lesson_list_queryset,
    get_lesson_progress,
)
from payments.models import Subscription


class CourseListView(ListAPIView):
    serializer_class = CourseListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    def get_queryset(self):
        return get_course_list_queryset(self.request.user)


class LessonListView(ListAPIView):
    serializer_class = LessonListSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Lesson.objects.none()
        return get_lesson_list_queryset(
            self.request.user, self.kwargs["course_slug"]
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
        ).prefetch_related(
            Prefetch(
                "assignments",
                queryset=Assignment.objects.filter(is_active=True),
            )
        )


class EnrollmentListView(ListAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_enrollment_queryset_with_progress(self.request.user)


class EnrollmentDetailView(RetrieveAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return get_enrollment_queryset_with_progress(self.request.user)


class CourseEnrollView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_slug):
        course = get_object_or_404(Course, slug=course_slug, is_active=True)
        enrollment, created = CourseEnrollment.objects.get_or_create(
            user=request.user, course=course
        )
        if not created and enrollment.status in (
            CourseEnrollment.CANCELED,
            CourseEnrollment.PAUSED,
        ):
            enrollment.status = CourseEnrollment.ACTIVE
            enrollment.last_activity_at = timezone.now()
            enrollment.save(
                update_fields=[
                    "status",
                    "last_activity_at",
                ]
            )
        enrollment = get_enrollment_queryset_with_progress(request.user).get(
            pk=enrollment.pk
        )
        serializer = EnrollmentSerializer(enrollment)
        return Response(
            serializer.data,
            status=(status.HTTP_201_CREATED if created else status.HTTP_200_OK),
        )


class CourseEnrollmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_slug):
        enrollment = get_object_or_404(
            get_enrollment_queryset_with_progress(request.user),
            course__slug=course_slug,
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
        enrollment = get_enrollment_queryset_with_progress(request.user).get(
            pk=enrollment.pk
        )
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
        enrollment = get_enrollment_queryset_with_progress(request.user).get(
            pk=enrollment.pk
        )
        serializer = EnrollmentSerializer(enrollment)
        return Response(serializer.data)


class AssignmentCompletionView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_assignment(self, course_slug, lesson_id, assignment_id):
        return get_object_or_404(
            Assignment.objects.select_related("lesson__course"),
            id=assignment_id,
            lesson_id=lesson_id,
            lesson__course__slug=course_slug,
            lesson__course__is_active=True,
            lesson__is_active=True,
            is_active=True,
        )

    def _check_access(self, request, assignment):
        enrollment = CourseEnrollment.objects.filter(
            user=request.user,
            course=assignment.lesson.course,
            status=CourseEnrollment.ACTIVE,
        ).exists()
        if not enrollment:
            raise PermissionDenied("Active enrollment required.")

        if not assignment.lesson.is_free:
            now = timezone.now()
            has_sub = Subscription.objects.filter(
                user=request.user,
                starts_at__lte=now,
                expires_at__gte=now,
            ).exists()
            if not has_sub:
                raise PermissionDenied(
                    "Active subscription required "
                    "to complete paid lesson "
                    "assignments."
                )

    def get(
        self,
        request,
        course_slug,
        lesson_id,
        assignment_id,
    ):
        assignment = self._get_assignment(course_slug, lesson_id, assignment_id)
        completion = get_object_or_404(
            CompletedAssignment,
            user=request.user,
            assignment=assignment,
        )
        return Response(AssignmentCompletionSerializer(completion).data)

    def post(
        self,
        request,
        course_slug,
        lesson_id,
        assignment_id,
    ):
        assignment = self._get_assignment(course_slug, lesson_id, assignment_id)
        self._check_access(request, assignment)

        serializer = AssignmentCompletionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        completion, created = complete_assignment(
            user=request.user,
            assignment=assignment,
            average_speed=serializer.validated_data["average_speed"],
            mistakes_count=serializer.validated_data["mistakes_count"],
        )

        data = AssignmentCompletionSerializer(completion).data
        data["lesson_progress"] = LessonProgressSerializer(
            get_lesson_progress(
                user=request.user,
                lesson=assignment.lesson,
            )
        ).data

        return Response(
            data,
            status=(status.HTTP_201_CREATED if created else status.HTTP_200_OK),
        )


class LessonProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_slug, lesson_id):
        lesson = get_object_or_404(
            Lesson.objects.select_related("course"),
            id=lesson_id,
            course__slug=course_slug,
            course__is_active=True,
            is_active=True,
        )

        if not CourseEnrollment.objects.filter(
            user=request.user,
            course=lesson.course,
        ).exists():
            raise PermissionDenied("Enrollment required.")

        progress = get_lesson_progress(
            user=request.user,
            lesson=lesson,
        )
        return Response(LessonProgressSerializer(progress).data)
