import pytest
from django.urls import reverse

from keypro.models import CompletedAssignment, Lesson


def lesson_detail_url(course_slug, lesson_pk):
    return reverse(
        "lesson-detail",
        kwargs={"course_slug": course_slug, "pk": lesson_pk},
    )


COURSE_LIST_URL = reverse("course-list")


@pytest.mark.django_db
class TestCourseListAnonymous:
    def test_anonymous_sees_courses(self, api_client, course):
        response = api_client.get(COURSE_LIST_URL)
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["slug"] == course.slug

    def test_anonymous_progress_fields_are_defaults(
        self, api_client, course, free_lesson
    ):
        response = api_client.get(COURSE_LIST_URL)
        data = response.data["results"][0]
        assert data["is_enrolled"] is False
        assert data["completed_lessons"] == 0
        assert data["progress_percent"] == 0.0
        assert data["total_lessons"] == 1


@pytest.mark.django_db
class TestCourseListAuthenticatedNotEnrolled:
    def test_not_enrolled_user(self, auth_client, course, free_lesson):
        response = auth_client.get(COURSE_LIST_URL)
        assert response.status_code == 200
        data = response.data["results"][0]
        assert data["is_enrolled"] is False
        assert data["completed_lessons"] == 0
        assert data["progress_percent"] == 0.0


@pytest.mark.django_db
class TestCourseListAuthenticatedEnrolled:
    def test_enrolled_user_no_completions(
        self, auth_client, course, free_lesson, enrollment
    ):
        response = auth_client.get(COURSE_LIST_URL)
        data = response.data["results"][0]
        assert data["is_enrolled"] is True
        assert data["completed_lessons"] == 0
        assert data["progress_percent"] == 0.0

    def test_enrolled_user_with_progress(
        self,
        auth_client,
        user,
        course,
        free_lesson,
        free_assignment,
        second_free_assignment,
        enrollment,
    ):
        CompletedAssignment.objects.create(
            user=user,
            assignment=free_assignment,
            average_speed=100,
            mistakes_count=2,
        )
        response = auth_client.get(COURSE_LIST_URL)
        data = response.data["results"][0]
        assert data["is_enrolled"] is True
        assert data["completed_lessons"] == 0
        assert data["progress_percent"] == 50.0

    def test_enrolled_user_fully_completed(
        self,
        auth_client,
        user,
        course,
        free_lesson,
        free_assignment,
        enrollment,
    ):
        CompletedAssignment.objects.create(
            user=user,
            assignment=free_assignment,
            average_speed=100,
            mistakes_count=2,
        )
        response = auth_client.get(COURSE_LIST_URL)
        data = response.data["results"][0]
        assert data["is_enrolled"] is True
        assert data["completed_lessons"] == 1
        assert data["progress_percent"] == 100.0


@pytest.mark.django_db
class TestLessonDetailViewAnonymousFreeLesson:
    def test_anonymous_can_access_free_lesson(
        self, api_client, free_lesson, free_assignment
    ):
        url = lesson_detail_url(free_lesson.course.slug, free_lesson.pk)
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data["id"] == free_lesson.pk
        assert len(response.data["assignments"]) == 1
        assert response.data["assignments"][0]["text_content"] == "Free content"


@pytest.mark.django_db
class TestLessonDetailViewAnonymousPaidLesson:
    def test_anonymous_cannot_access_paid_lesson(self, api_client, paid_lesson):
        url = lesson_detail_url(paid_lesson.course.slug, paid_lesson.pk)
        response = api_client.get(url)
        assert response.status_code == 401


@pytest.mark.django_db
class TestLessonDetailViewAuthenticatedFreeLesson:
    def test_authenticated_can_access_free_lesson(
        self, auth_client, free_lesson, free_assignment
    ):
        url = lesson_detail_url(free_lesson.course.slug, free_lesson.pk)
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.data["id"] == free_lesson.pk


@pytest.mark.django_db
class TestLessonDetailViewAuthenticatedPaidLessonNoSubscription:
    def test_authenticated_without_subscription_cannot_access_paid_lesson(
        self, auth_client, paid_lesson
    ):
        url = lesson_detail_url(paid_lesson.course.slug, paid_lesson.pk)
        response = auth_client.get(url)
        assert response.status_code == 403

    def test_error_message_mentions_subscription(
        self, auth_client, paid_lesson
    ):
        url = lesson_detail_url(paid_lesson.course.slug, paid_lesson.pk)
        response = auth_client.get(url)
        assert "subscription" in response.data["detail"].lower()


@pytest.mark.django_db
class TestLessonDetailViewAuthenticatedPaidLessonWithSubscription:
    def test_subscriber_can_access_paid_lesson(
        self,
        auth_client,
        paid_lesson,
        paid_assignment,
        active_subscription,
    ):
        url = lesson_detail_url(paid_lesson.course.slug, paid_lesson.pk)
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.data["id"] == paid_lesson.pk
        assert len(response.data["assignments"]) == 1
        assert response.data["assignments"][0]["text_content"] == "Paid content"

    def test_expired_subscriber_cannot_access_paid_lesson(
        self, auth_client, paid_lesson, expired_subscription
    ):
        url = lesson_detail_url(paid_lesson.course.slug, paid_lesson.pk)
        response = auth_client.get(url)
        assert response.status_code == 403


@pytest.mark.django_db
class TestLessonDetailViewInactiveLesson:
    def test_inactive_lesson_returns_404(self, api_client, course):
        lesson = Lesson.objects.create(
            course=course,
            title="Inactive",
            order=3,
            is_free=True,
            is_active=False,
        )
        url = lesson_detail_url(course.slug, lesson.pk)
        response = api_client.get(url)
        assert response.status_code == 404
