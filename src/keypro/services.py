from django.db import transaction
from django.db.models import (
    BooleanField,
    Case,
    Count,
    Exists,
    F,
    OuterRef,
    Q,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Coalesce
from django.utils import timezone

from keypro.models import (
    Assignment,
    CompletedAssignment,
    Course,
    CourseEnrollment,
    Lesson,
)


def get_course_list_queryset(user):
    qs = Course.objects.filter(is_active=True).annotate(
        total_lessons=Count("lessons", filter=Q(lessons__is_active=True)),
    )

    if user.is_authenticated:
        total_assignments_sq = (
            Assignment.objects.filter(
                lesson__course__pk=OuterRef("pk"),
                lesson__is_active=True,
                is_active=True,
            )
            .order_by()
            .values("lesson__course")
            .annotate(cnt=Count("id"))
            .values("cnt")
        )

        completed_assignments_sq = (
            CompletedAssignment.objects.filter(
                user=user,
                assignment__lesson__course__pk=OuterRef("pk"),
                assignment__lesson__is_active=True,
                assignment__is_active=True,
            )
            .order_by()
            .values("assignment__lesson__course")
            .annotate(cnt=Count("id"))
            .values("cnt")
        )

        completed_lessons_sq = (
            Lesson.objects.filter(
                course=OuterRef("pk"),
                is_active=True,
            )
            .annotate(
                active_count=Count(
                    "assignments",
                    filter=Q(assignments__is_active=True),
                    distinct=True,
                ),
                completed_count=Count(
                    "assignments__completions",
                    filter=Q(
                        assignments__is_active=True,
                        assignments__completions__user=user,
                    ),
                    distinct=True,
                ),
            )
            .filter(
                active_count__gt=0,
                completed_count__gte=F("active_count"),
            )
            .order_by()
            .values("course")
            .annotate(cnt=Count("id"))
            .values("cnt")
        )

        qs = qs.annotate(
            is_enrolled=Exists(
                CourseEnrollment.objects.filter(
                    user=user,
                    course=OuterRef("pk"),
                    status=CourseEnrollment.ACTIVE,
                )
            ),
            total_assignments=Coalesce(
                Subquery(total_assignments_sq), Value(0)
            ),
            completed_assignments=Coalesce(
                Subquery(completed_assignments_sq), Value(0)
            ),
            completed_lessons=Coalesce(
                Subquery(completed_lessons_sq), Value(0)
            ),
        )
    else:
        qs = qs.annotate(
            is_enrolled=Value(False),
            total_assignments=Value(0),
            completed_assignments=Value(0),
            completed_lessons=Value(0),
        )

    return qs


def get_lesson_list_queryset(user, course_slug):
    qs = Lesson.objects.filter(
        course__slug=course_slug,
        is_active=True,
    )

    has_active_enrollment = (
        user.is_authenticated
        and CourseEnrollment.objects.filter(
            user=user,
            course__slug=course_slug,
            status=CourseEnrollment.ACTIVE,
        ).exists()
    )

    if has_active_enrollment:
        qs = qs.annotate(
            _active_count=Count(
                "assignments",
                filter=Q(assignments__is_active=True),
                distinct=True,
            ),
            _completed_count=Count(
                "assignments__completions",
                filter=Q(
                    assignments__is_active=True,
                    assignments__completions__user=user,
                ),
                distinct=True,
            ),
            is_completed=Case(
                When(
                    _active_count__gt=0,
                    _completed_count__gte=F("_active_count"),
                    then=Value(True),
                ),
                default=Value(False),
                output_field=BooleanField(),
            ),
        )
    else:
        qs = qs.annotate(
            is_completed=Value(None, output_field=BooleanField()),
        )

    return qs


def complete_assignment(*, user, assignment, average_speed, mistakes_count):
    with transaction.atomic():
        completion, created = CompletedAssignment.objects.update_or_create(
            user=user,
            assignment=assignment,
            defaults={
                "action_type": (CompletedAssignment.ActionType.COMPLETE),
                "average_speed": average_speed,
                "mistakes_count": mistakes_count,
                "completed_at": timezone.now(),
            },
        )

        course = assignment.lesson.course
        enrollment = CourseEnrollment.objects.get(user=user, course=course)
        enrollment.last_activity_at = timezone.now()
        enrollment.save(update_fields=["last_activity_at"])

        _maybe_complete_enrollment(enrollment, course, user)

    return completion, created


def _maybe_complete_enrollment(enrollment, course, user):
    total = Assignment.objects.filter(
        lesson__course=course,
        lesson__is_active=True,
        is_active=True,
    ).count()

    if total == 0:
        return

    completed = CompletedAssignment.objects.filter(
        user=user,
        assignment__lesson__course=course,
        assignment__lesson__is_active=True,
        assignment__is_active=True,
    ).count()

    if completed >= total:
        enrollment.status = CourseEnrollment.COMPLETED
        enrollment.completed_at = timezone.now()
        enrollment.save(update_fields=["status", "completed_at"])


def get_lesson_progress(*, user, lesson):
    total = lesson.assignments.filter(is_active=True).count()

    completed_qs = CompletedAssignment.objects.filter(
        user=user,
        assignment__lesson=lesson,
        assignment__is_active=True,
    )
    completed = completed_qs.count()

    if total > 0 and completed >= total:
        status = "completed"
        completed_at = (
            completed_qs.order_by("-completed_at")
            .values_list("completed_at", flat=True)
            .first()
        )
    else:
        status = "in_progress"
        completed_at = None

    return {
        "lesson_id": lesson.id,
        "status": status,
        "completed_assignments": completed,
        "total_assignments": total,
        "progress_percent": (
            round((completed / total) * 100, 1) if total > 0 else 0.0
        ),
        "completed_at": completed_at,
    }


def get_enrollment_queryset_with_progress(user):
    total_assignments_sq = (
        Assignment.objects.filter(
            lesson__course__pk=OuterRef("course_id"),
            lesson__is_active=True,
            is_active=True,
        )
        .order_by()
        .values("lesson__course")
        .annotate(cnt=Count("id"))
        .values("cnt")
    )

    completed_assignments_sq = (
        CompletedAssignment.objects.filter(
            user=user,
            assignment__lesson__course__pk=OuterRef("course_id"),
            assignment__lesson__is_active=True,
            assignment__is_active=True,
        )
        .order_by()
        .values("assignment__lesson__course")
        .annotate(cnt=Count("id"))
        .values("cnt")
    )

    total_lessons_sq = (
        Lesson.objects.filter(
            course__pk=OuterRef("course_id"),
            is_active=True,
        )
        .order_by()
        .values("course")
        .annotate(cnt=Count("id"))
        .values("cnt")
    )

    completed_lessons_sq = (
        Lesson.objects.filter(
            course__pk=OuterRef("course_id"),
            is_active=True,
        )
        .annotate(
            active_count=Count(
                "assignments",
                filter=Q(assignments__is_active=True),
                distinct=True,
            ),
            completed_count=Count(
                "assignments__completions",
                filter=Q(
                    assignments__is_active=True,
                    assignments__completions__user=user,
                ),
                distinct=True,
            ),
        )
        .filter(
            active_count__gt=0,
            completed_count__gte=F("active_count"),
        )
        .order_by()
        .values("course")
        .annotate(cnt=Count("id"))
        .values("cnt")
    )

    current_lesson_id_sq = (
        Lesson.objects.filter(
            course__pk=OuterRef("course_id"),
            is_active=True,
        )
        .annotate(
            active_count=Count(
                "assignments",
                filter=Q(assignments__is_active=True),
                distinct=True,
            ),
            completed_count=Count(
                "assignments__completions",
                filter=Q(
                    assignments__is_active=True,
                    assignments__completions__user=user,
                ),
                distinct=True,
            ),
        )
        .filter(active_count__gt=0)
        .exclude(active_count=F("completed_count"))
        .order_by("order")
        .values("id")[:1]
    )

    return (
        CourseEnrollment.objects.filter(user=user)
        .select_related("course")
        .annotate(
            total_assignments=Coalesce(
                Subquery(total_assignments_sq),
                Value(0),
            ),
            completed_assignments=Coalesce(
                Subquery(completed_assignments_sq),
                Value(0),
            ),
            total_lessons=Coalesce(
                Subquery(total_lessons_sq),
                Value(0),
            ),
            completed_lessons=Coalesce(
                Subquery(completed_lessons_sq),
                Value(0),
            ),
            current_lesson_id=Subquery(current_lesson_id_sq),
        )
    )
