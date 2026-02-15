from datetime import timedelta

import pytest
from django.utils import timezone

from keypro.models import Course, Lesson
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
        text_content="Free content",
        order=1,
        is_free=True,
        is_active=True,
    )


@pytest.fixture
def paid_lesson(course):
    return Lesson.objects.create(
        course=course,
        title="Paid Lesson",
        text_content="Paid content",
        order=2,
        is_free=False,
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
