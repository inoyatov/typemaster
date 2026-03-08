import pytest

from keypro.models import (
    Assignment,
    CompletedAssignment,
    CourseEnrollment,
)


@pytest.mark.django_db
class TestLessonProgressAuth:
    def test_401_unauthenticated(
        self, api_client, lesson_progress_url, free_lesson
    ):
        url = lesson_progress_url(free_lesson.course.slug, free_lesson.id)
        assert api_client.get(url).status_code == 401


@pytest.mark.django_db
class TestLessonProgressEnrollment:
    def test_403_not_enrolled(
        self,
        auth_client,
        lesson_progress_url,
        free_lesson,
    ):
        url = lesson_progress_url(free_lesson.course.slug, free_lesson.id)
        response = auth_client.get(url)
        assert response.status_code == 403


@pytest.mark.django_db
class TestLessonProgressComputation:
    def test_zero_progress(
        self,
        auth_client,
        lesson_progress_url,
        free_lesson,
        free_assignment,
        enrollment,
    ):
        url = lesson_progress_url(free_lesson.course.slug, free_lesson.id)
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.data["completed_assignments"] == 0
        assert response.data["total_assignments"] == 1
        assert response.data["progress_percent"] == 0.0
        assert response.data["status"] == "in_progress"

    def test_partial_progress(
        self,
        auth_client,
        user,
        lesson_progress_url,
        free_lesson,
        free_assignment,
        second_free_assignment,
        enrollment,
    ):
        CompletedAssignment.objects.create(
            user=user,
            assignment=free_assignment,
            average_speed=120,
            mistakes_count=0,
        )
        url = lesson_progress_url(free_lesson.course.slug, free_lesson.id)
        response = auth_client.get(url)
        assert response.data["completed_assignments"] == 1
        assert response.data["total_assignments"] == 2
        assert response.data["progress_percent"] == 50.0
        assert response.data["status"] == "in_progress"

    def test_full_completion(
        self,
        auth_client,
        user,
        lesson_progress_url,
        free_lesson,
        free_assignment,
        enrollment,
    ):
        CompletedAssignment.objects.create(
            user=user,
            assignment=free_assignment,
            average_speed=120,
            mistakes_count=0,
        )
        url = lesson_progress_url(free_lesson.course.slug, free_lesson.id)
        response = auth_client.get(url)
        assert response.data["status"] == "completed"
        assert response.data["progress_percent"] == 100.0
        assert response.data["completed_at"] is not None

    def test_response_shape(
        self,
        auth_client,
        lesson_progress_url,
        free_lesson,
        free_assignment,
        enrollment,
    ):
        url = lesson_progress_url(free_lesson.course.slug, free_lesson.id)
        response = auth_client.get(url)
        expected_fields = {
            "lesson_id",
            "status",
            "completed_assignments",
            "total_assignments",
            "progress_percent",
            "completed_at",
        }
        assert set(response.data.keys()) == expected_fields

    def test_inactive_assignments_excluded(
        self,
        auth_client,
        lesson_progress_url,
        free_lesson,
        free_assignment,
        enrollment,
    ):
        Assignment.objects.create(
            lesson=free_lesson,
            title="Inactive",
            text_content="t",
            order=10,
            is_active=False,
        )
        url = lesson_progress_url(free_lesson.course.slug, free_lesson.id)
        response = auth_client.get(url)
        assert response.data["total_assignments"] == 1

    def test_canceled_enrollment_can_view_progress(
        self,
        auth_client,
        lesson_progress_url,
        free_lesson,
        free_assignment,
        enrollment,
    ):
        enrollment.status = CourseEnrollment.CANCELED
        enrollment.save()
        url = lesson_progress_url(free_lesson.course.slug, free_lesson.id)
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_no_active_assignments_returns_zero(
        self,
        auth_client,
        lesson_progress_url,
        free_lesson,
        enrollment,
    ):
        url = lesson_progress_url(free_lesson.course.slug, free_lesson.id)
        response = auth_client.get(url)
        assert response.data["total_assignments"] == 0
        assert response.data["progress_percent"] == 0.0
