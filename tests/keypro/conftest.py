from datetime import timedelta

import pytest
from django.utils import timezone

from keypro.models import Assignment, Course, CourseEnrollment, Lesson
from payments.models import Subscription, SubscriptionPlan


@pytest.fixture
def course(db):
    return Course.objects.create(
        title="Test Course",
        slug="test-course",
        is_active=True,
    )


@pytest.fixture
def free_lesson(course):
    return Lesson.objects.create(
        course=course,
        title="Free Lesson",
        order=1,
        is_free=True,
        is_active=True,
    )


@pytest.fixture
def paid_lesson(course):
    return Lesson.objects.create(
        course=course,
        title="Paid Lesson",
        order=2,
        is_free=False,
        is_active=True,
    )


@pytest.fixture
def free_assignment(free_lesson):
    return Assignment.objects.create(
        lesson=free_lesson,
        title="Free Assignment",
        text_content="Free content",
        order=1,
        is_active=True,
    )


@pytest.fixture
def paid_assignment(paid_lesson):
    return Assignment.objects.create(
        lesson=paid_lesson,
        title="Paid Assignment",
        text_content="Paid content",
        order=1,
        is_active=True,
    )


@pytest.fixture
def active_subscription(user):
    now = timezone.now()
    plan = SubscriptionPlan.objects.create(
        name="Monthly",
        duration_days=30,
        price=9.99,
    )
    return Subscription.objects.create(
        user=user,
        plan=plan,
        starts_at=now - timedelta(days=1),
        expires_at=now + timedelta(days=29),
    )


@pytest.fixture
def expired_subscription(user):
    now = timezone.now()
    plan = SubscriptionPlan.objects.create(
        name="Monthly",
        duration_days=30,
        price=9.99,
    )
    return Subscription.objects.create(
        user=user,
        plan=plan,
        starts_at=now - timedelta(days=31),
        expires_at=now - timedelta(days=1),
    )


@pytest.fixture
def second_free_assignment(free_lesson):
    return Assignment.objects.create(
        lesson=free_lesson,
        title="Second Free Assignment",
        text_content="More free content",
        order=2,
        is_active=True,
    )


@pytest.fixture
def enrollment(user, course):
    return CourseEnrollment.objects.create(user=user, course=course)


@pytest.fixture
def canceled_enrollment(user, course):
    return CourseEnrollment.objects.create(
        user=user,
        course=course,
        status=CourseEnrollment.CANCELED,
    )


@pytest.fixture
def completion_url():
    def _url(course_slug, lesson_id, assignment_id):
        return (
            f"/api/courses/{course_slug}/lessons/"
            f"{lesson_id}/assignments/"
            f"{assignment_id}/completion/"
        )

    return _url


@pytest.fixture
def lesson_progress_url():
    def _url(course_slug, lesson_id):
        return f"/api/courses/{course_slug}/lessons/{lesson_id}/progress/"

    return _url


@pytest.fixture
def valid_completion_data():
    return {
        "action_type": "complete",
        "average_speed": 120,
        "mistakes_count": 3,
    }
