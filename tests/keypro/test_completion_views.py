import pytest

from keypro.models import (
    Assignment,
    CompletedAssignment,
    Course,
    CourseEnrollment,
    Lesson,
)


@pytest.mark.django_db
class TestCompletionAuth:
    def test_post_requires_auth(
        self, api_client, completion_url, free_assignment
    ):
        url = completion_url(
            free_assignment.lesson.course.slug,
            free_assignment.lesson.id,
            free_assignment.id,
        )
        assert api_client.post(url).status_code == 401

    def test_get_requires_auth(
        self, api_client, completion_url, free_assignment
    ):
        url = completion_url(
            free_assignment.lesson.course.slug,
            free_assignment.lesson.id,
            free_assignment.id,
        )
        assert api_client.get(url).status_code == 401


@pytest.mark.django_db
class TestCompletionHierarchy:
    def test_404_wrong_course_slug(
        self,
        auth_client,
        completion_url,
        free_assignment,
        enrollment,
        valid_completion_data,
    ):
        url = completion_url(
            "wrong-slug",
            free_assignment.lesson.id,
            free_assignment.id,
        )
        response = auth_client.post(url, valid_completion_data, format="json")
        assert response.status_code == 404

    def test_404_wrong_lesson_id(
        self,
        auth_client,
        completion_url,
        free_assignment,
        enrollment,
        valid_completion_data,
    ):
        url = completion_url(
            free_assignment.lesson.course.slug,
            9999,
            free_assignment.id,
        )
        response = auth_client.post(url, valid_completion_data, format="json")
        assert response.status_code == 404

    def test_404_wrong_assignment_id(
        self,
        auth_client,
        completion_url,
        free_assignment,
        enrollment,
        valid_completion_data,
    ):
        url = completion_url(
            free_assignment.lesson.course.slug,
            free_assignment.lesson.id,
            9999,
        )
        response = auth_client.post(url, valid_completion_data, format="json")
        assert response.status_code == 404

    def test_404_inactive_course(
        self,
        auth_client,
        completion_url,
        valid_completion_data,
        user,
    ):
        course = Course.objects.create(
            title="Inactive",
            slug="inactive",
            is_active=False,
        )
        lesson = Lesson.objects.create(
            course=course,
            title="L",
            order=1,
            is_active=True,
            is_free=True,
        )
        assignment = Assignment.objects.create(
            lesson=lesson,
            title="A",
            text_content="t",
            order=1,
            is_active=True,
        )
        CourseEnrollment.objects.create(user=user, course=course)
        url = completion_url(course.slug, lesson.id, assignment.id)
        response = auth_client.post(url, valid_completion_data, format="json")
        assert response.status_code == 404

    def test_404_inactive_lesson(
        self,
        auth_client,
        completion_url,
        valid_completion_data,
        course,
        enrollment,
    ):
        lesson = Lesson.objects.create(
            course=course,
            title="Inactive Lesson",
            order=10,
            is_active=False,
            is_free=True,
        )
        assignment = Assignment.objects.create(
            lesson=lesson,
            title="A",
            text_content="t",
            order=1,
            is_active=True,
        )
        url = completion_url(course.slug, lesson.id, assignment.id)
        response = auth_client.post(url, valid_completion_data, format="json")
        assert response.status_code == 404

    def test_404_inactive_assignment(
        self,
        auth_client,
        completion_url,
        valid_completion_data,
        free_lesson,
        enrollment,
    ):
        assignment = Assignment.objects.create(
            lesson=free_lesson,
            title="Inactive",
            text_content="t",
            order=10,
            is_active=False,
        )
        url = completion_url(
            free_lesson.course.slug,
            free_lesson.id,
            assignment.id,
        )
        response = auth_client.post(url, valid_completion_data, format="json")
        assert response.status_code == 404


@pytest.mark.django_db
class TestCompletionEnrollment:
    def test_403_no_enrollment(
        self,
        auth_client,
        completion_url,
        free_assignment,
        valid_completion_data,
    ):
        url = completion_url(
            free_assignment.lesson.course.slug,
            free_assignment.lesson.id,
            free_assignment.id,
        )
        response = auth_client.post(url, valid_completion_data, format="json")
        assert response.status_code == 403

    def test_403_canceled_enrollment(
        self,
        auth_client,
        completion_url,
        free_assignment,
        enrollment,
        valid_completion_data,
    ):
        enrollment.status = CourseEnrollment.CANCELED
        enrollment.save()
        url = completion_url(
            free_assignment.lesson.course.slug,
            free_assignment.lesson.id,
            free_assignment.id,
        )
        response = auth_client.post(url, valid_completion_data, format="json")
        assert response.status_code == 403

    def test_403_paused_enrollment(
        self,
        auth_client,
        completion_url,
        free_assignment,
        enrollment,
        valid_completion_data,
    ):
        enrollment.status = CourseEnrollment.PAUSED
        enrollment.save()
        url = completion_url(
            free_assignment.lesson.course.slug,
            free_assignment.lesson.id,
            free_assignment.id,
        )
        response = auth_client.post(url, valid_completion_data, format="json")
        assert response.status_code == 403

    def test_403_completed_enrollment(
        self,
        auth_client,
        completion_url,
        free_assignment,
        enrollment,
        valid_completion_data,
    ):
        enrollment.status = CourseEnrollment.COMPLETED
        enrollment.save()
        url = completion_url(
            free_assignment.lesson.course.slug,
            free_assignment.lesson.id,
            free_assignment.id,
        )
        response = auth_client.post(url, valid_completion_data, format="json")
        assert response.status_code == 403


@pytest.mark.django_db
class TestCompletionFreeLesson:
    def test_201_creates_completion(
        self,
        auth_client,
        completion_url,
        free_assignment,
        enrollment,
        valid_completion_data,
    ):
        url = completion_url(
            free_assignment.lesson.course.slug,
            free_assignment.lesson.id,
            free_assignment.id,
        )
        response = auth_client.post(url, valid_completion_data, format="json")
        assert response.status_code == 201
        assert response.data["action_type"] == "complete"
        assert response.data["average_speed"] == 120
        assert response.data["mistakes_count"] == 3

    def test_200_idempotent_update(
        self,
        auth_client,
        user,
        completion_url,
        free_assignment,
        second_free_assignment,
        enrollment,
        valid_completion_data,
    ):
        url = completion_url(
            free_assignment.lesson.course.slug,
            free_assignment.lesson.id,
            free_assignment.id,
        )
        auth_client.post(url, valid_completion_data, format="json")
        updated_data = {
            "action_type": "complete",
            "average_speed": 200,
            "mistakes_count": 1,
        }
        response = auth_client.post(url, updated_data, format="json")
        assert response.status_code == 200
        assert response.data["average_speed"] == 200
        assert response.data["mistakes_count"] == 1
        assert (
            CompletedAssignment.objects.filter(
                user=user, assignment=free_assignment
            ).count()
            == 1
        )

    def test_response_includes_lesson_progress(
        self,
        auth_client,
        completion_url,
        free_assignment,
        enrollment,
        valid_completion_data,
    ):
        url = completion_url(
            free_assignment.lesson.course.slug,
            free_assignment.lesson.id,
            free_assignment.id,
        )
        response = auth_client.post(url, valid_completion_data, format="json")
        assert "lesson_progress" in response.data
        lp = response.data["lesson_progress"]
        assert lp["lesson_id"] == free_assignment.lesson.id
        assert lp["completed_assignments"] == 1
        assert "progress_percent" in lp


@pytest.mark.django_db
class TestCompletionPaidLesson:
    def test_403_no_subscription(
        self,
        auth_client,
        completion_url,
        paid_assignment,
        enrollment,
        valid_completion_data,
    ):
        url = completion_url(
            paid_assignment.lesson.course.slug,
            paid_assignment.lesson.id,
            paid_assignment.id,
        )
        response = auth_client.post(url, valid_completion_data, format="json")
        assert response.status_code == 403

    def test_201_with_active_subscription(
        self,
        auth_client,
        completion_url,
        paid_assignment,
        enrollment,
        active_subscription,
        valid_completion_data,
    ):
        url = completion_url(
            paid_assignment.lesson.course.slug,
            paid_assignment.lesson.id,
            paid_assignment.id,
        )
        response = auth_client.post(url, valid_completion_data, format="json")
        assert response.status_code == 201

    def test_403_with_expired_subscription(
        self,
        auth_client,
        completion_url,
        paid_assignment,
        enrollment,
        expired_subscription,
        valid_completion_data,
    ):
        url = completion_url(
            paid_assignment.lesson.course.slug,
            paid_assignment.lesson.id,
            paid_assignment.id,
        )
        response = auth_client.post(url, valid_completion_data, format="json")
        assert response.status_code == 403


@pytest.mark.django_db
class TestCompletionValidation:
    def test_missing_action_type(
        self,
        auth_client,
        completion_url,
        free_assignment,
        enrollment,
    ):
        url = completion_url(
            free_assignment.lesson.course.slug,
            free_assignment.lesson.id,
            free_assignment.id,
        )
        data = {"average_speed": 120, "mistakes_count": 0}
        response = auth_client.post(url, data, format="json")
        assert response.status_code == 400

    def test_invalid_action_type(
        self,
        auth_client,
        completion_url,
        free_assignment,
        enrollment,
    ):
        url = completion_url(
            free_assignment.lesson.course.slug,
            free_assignment.lesson.id,
            free_assignment.id,
        )
        data = {
            "action_type": "invalid",
            "average_speed": 120,
            "mistakes_count": 0,
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == 400

    def test_zero_average_speed_rejected(
        self,
        auth_client,
        completion_url,
        free_assignment,
        enrollment,
    ):
        url = completion_url(
            free_assignment.lesson.course.slug,
            free_assignment.lesson.id,
            free_assignment.id,
        )
        data = {
            "action_type": "complete",
            "average_speed": 0,
            "mistakes_count": 0,
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == 400

    def test_negative_average_speed_rejected(
        self,
        auth_client,
        completion_url,
        free_assignment,
        enrollment,
    ):
        url = completion_url(
            free_assignment.lesson.course.slug,
            free_assignment.lesson.id,
            free_assignment.id,
        )
        data = {
            "action_type": "complete",
            "average_speed": -1,
            "mistakes_count": 0,
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == 400

    def test_negative_mistakes_count_rejected(
        self,
        auth_client,
        completion_url,
        free_assignment,
        enrollment,
    ):
        url = completion_url(
            free_assignment.lesson.course.slug,
            free_assignment.lesson.id,
            free_assignment.id,
        )
        data = {
            "action_type": "complete",
            "average_speed": 120,
            "mistakes_count": -1,
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == 400

    def test_zero_mistakes_count_accepted(
        self,
        auth_client,
        completion_url,
        free_assignment,
        enrollment,
    ):
        url = completion_url(
            free_assignment.lesson.course.slug,
            free_assignment.lesson.id,
            free_assignment.id,
        )
        data = {
            "action_type": "complete",
            "average_speed": 120,
            "mistakes_count": 0,
        }
        response = auth_client.post(url, data, format="json")
        assert response.status_code == 201


@pytest.mark.django_db
class TestCompletionGet:
    def test_200_existing_completion(
        self,
        auth_client,
        user,
        completion_url,
        free_assignment,
    ):
        CompletedAssignment.objects.create(
            user=user,
            assignment=free_assignment,
            average_speed=120,
            mistakes_count=3,
        )
        url = completion_url(
            free_assignment.lesson.course.slug,
            free_assignment.lesson.id,
            free_assignment.id,
        )
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.data["average_speed"] == 120

    def test_404_no_completion(
        self,
        auth_client,
        completion_url,
        free_assignment,
    ):
        url = completion_url(
            free_assignment.lesson.course.slug,
            free_assignment.lesson.id,
            free_assignment.id,
        )
        response = auth_client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestCompletionSideEffects:
    def test_updates_last_activity_at(
        self,
        auth_client,
        completion_url,
        free_assignment,
        enrollment,
        valid_completion_data,
    ):
        old_activity = enrollment.last_activity_at
        url = completion_url(
            free_assignment.lesson.course.slug,
            free_assignment.lesson.id,
            free_assignment.id,
        )
        auth_client.post(url, valid_completion_data, format="json")
        enrollment.refresh_from_db()
        assert enrollment.last_activity_at > old_activity

    def test_auto_completes_enrollment(
        self,
        auth_client,
        user,
        completion_url,
        free_assignment,
        enrollment,
        valid_completion_data,
    ):
        url = completion_url(
            free_assignment.lesson.course.slug,
            free_assignment.lesson.id,
            free_assignment.id,
        )
        auth_client.post(url, valid_completion_data, format="json")
        enrollment.refresh_from_db()
        assert enrollment.status == CourseEnrollment.COMPLETED
        assert enrollment.completed_at is not None

    def test_lesson_status_completed(
        self,
        auth_client,
        completion_url,
        free_assignment,
        enrollment,
        valid_completion_data,
    ):
        url = completion_url(
            free_assignment.lesson.course.slug,
            free_assignment.lesson.id,
            free_assignment.id,
        )
        response = auth_client.post(url, valid_completion_data, format="json")
        lp = response.data["lesson_progress"]
        assert lp["status"] == "completed"
        assert lp["progress_percent"] == 100.0
