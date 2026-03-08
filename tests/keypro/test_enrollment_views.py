import pytest
from django.urls import reverse

from accounts.models import User
from keypro.models import (
    Assignment,
    CompletedAssignment,
    Course,
    CourseEnrollment,
    Lesson,
)


@pytest.mark.django_db
class TestEnrollmentAuth:
    def test_enrollment_list_requires_auth(self, api_client):
        url = reverse("enrollment-list")
        assert api_client.get(url).status_code == 401

    def test_enrollment_detail_requires_auth(self, api_client, enrollment):
        url = reverse("enrollment-detail", kwargs={"pk": enrollment.pk})
        assert api_client.get(url).status_code == 401

    def test_course_enroll_requires_auth(self, api_client, course):
        url = reverse("course-enroll", kwargs={"course_id": course.id})
        assert api_client.post(url).status_code == 401

    def test_course_enrollment_detail_requires_auth(self, api_client, course):
        url = reverse(
            "course-enrollment-detail", kwargs={"course_id": course.id}
        )
        assert api_client.get(url).status_code == 401

    def test_enrollment_cancel_requires_auth(self, api_client, enrollment):
        url = reverse("enrollment-cancel", kwargs={"pk": enrollment.pk})
        assert api_client.post(url).status_code == 401

    def test_enrollment_resume_requires_auth(self, api_client, enrollment):
        url = reverse("enrollment-resume", kwargs={"pk": enrollment.pk})
        assert api_client.post(url).status_code == 401


@pytest.mark.django_db
class TestEnrollmentList:
    def test_returns_own_enrollments(self, auth_client, enrollment):
        url = reverse("enrollment-list")
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == enrollment.id

    def test_excludes_other_users_enrollments(
        self, auth_client, course, enrollment
    ):
        other_user = User.objects.create_user(
            email="other@example.com",
            password="pass123",
            first_name="Other",
            last_name="User",
        )
        other_course = Course.objects.create(
            title="Other", slug="other", is_active=True
        )
        CourseEnrollment.objects.create(user=other_user, course=other_course)
        url = reverse("enrollment-list")
        response = auth_client.get(url)
        assert response.data["count"] == 1
        assert response.data["results"][0]["id"] == enrollment.id


@pytest.mark.django_db
class TestEnrollmentDetail:
    def test_returns_enrollment(self, auth_client, enrollment):
        url = reverse("enrollment-detail", kwargs={"pk": enrollment.pk})
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.data["id"] == enrollment.id

    def test_404_for_other_users_enrollment(self, auth_client, course):
        other_user = User.objects.create_user(
            email="other@example.com",
            password="pass123",
            first_name="Other",
            last_name="User",
        )
        other_enrollment = CourseEnrollment.objects.create(
            user=other_user, course=course
        )
        url = reverse("enrollment-detail", kwargs={"pk": other_enrollment.pk})
        response = auth_client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestCourseEnroll:
    def test_creates_new_enrollment(self, auth_client, course):
        url = reverse("course-enroll", kwargs={"course_id": course.id})
        response = auth_client.post(url)
        assert response.status_code == 201
        assert response.data["status"] == "active"
        assert response.data["course"]["id"] == course.id

    def test_returns_existing_active_enrollment(self, auth_client, enrollment):
        url = reverse(
            "course-enroll", kwargs={"course_id": enrollment.course.id}
        )
        response = auth_client.post(url)
        assert response.status_code == 200
        assert response.data["status"] == "active"

    def test_reactivates_canceled_enrollment(self, auth_client, enrollment):
        enrollment.status = CourseEnrollment.CANCELED
        enrollment.save()
        url = reverse(
            "course-enroll", kwargs={"course_id": enrollment.course.id}
        )
        response = auth_client.post(url)
        assert response.status_code == 200
        assert response.data["status"] == "active"

    def test_reactivates_paused_enrollment(self, auth_client, enrollment):
        enrollment.status = CourseEnrollment.PAUSED
        enrollment.save()
        url = reverse(
            "course-enroll", kwargs={"course_id": enrollment.course.id}
        )
        response = auth_client.post(url)
        assert response.status_code == 200
        assert response.data["status"] == "active"

    def test_returns_existing_completed_enrollment(
        self, auth_client, enrollment
    ):
        enrollment.status = CourseEnrollment.COMPLETED
        enrollment.save()
        url = reverse(
            "course-enroll", kwargs={"course_id": enrollment.course.id}
        )
        response = auth_client.post(url)
        assert response.status_code == 200
        assert response.data["status"] == "completed"

    def test_404_for_inactive_course(self, auth_client):
        course = Course.objects.create(
            title="Inactive", slug="inactive", is_active=False
        )
        url = reverse("course-enroll", kwargs={"course_id": course.id})
        response = auth_client.post(url)
        assert response.status_code == 404

    def test_404_for_nonexistent_course(self, auth_client):
        url = reverse("course-enroll", kwargs={"course_id": 99999})
        response = auth_client.post(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestCourseEnrollmentDetail:
    def test_returns_enrollment(self, auth_client, enrollment):
        url = reverse(
            "course-enrollment-detail",
            kwargs={"course_id": enrollment.course.id},
        )
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.data["id"] == enrollment.id

    def test_404_if_not_enrolled(self, auth_client, course):
        url = reverse(
            "course-enrollment-detail", kwargs={"course_id": course.id}
        )
        response = auth_client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestEnrollmentCancel:
    def test_cancel_active(self, auth_client, enrollment):
        url = reverse("enrollment-cancel", kwargs={"pk": enrollment.pk})
        response = auth_client.post(url)
        assert response.status_code == 200
        assert response.data["status"] == "canceled"

    def test_cancel_paused(self, auth_client, enrollment):
        enrollment.status = CourseEnrollment.PAUSED
        enrollment.save()
        url = reverse("enrollment-cancel", kwargs={"pk": enrollment.pk})
        response = auth_client.post(url)
        assert response.status_code == 200
        assert response.data["status"] == "canceled"

    def test_cancel_already_canceled_returns_400(self, auth_client, enrollment):
        enrollment.status = CourseEnrollment.CANCELED
        enrollment.save()
        url = reverse("enrollment-cancel", kwargs={"pk": enrollment.pk})
        response = auth_client.post(url)
        assert response.status_code == 400

    def test_cancel_completed_returns_400(self, auth_client, enrollment):
        enrollment.status = CourseEnrollment.COMPLETED
        enrollment.save()
        url = reverse("enrollment-cancel", kwargs={"pk": enrollment.pk})
        response = auth_client.post(url)
        assert response.status_code == 400


@pytest.mark.django_db
class TestEnrollmentResume:
    def test_resume_canceled(self, auth_client, enrollment):
        enrollment.status = CourseEnrollment.CANCELED
        enrollment.save()
        url = reverse("enrollment-resume", kwargs={"pk": enrollment.pk})
        response = auth_client.post(url)
        assert response.status_code == 200
        assert response.data["status"] == "active"

    def test_resume_paused(self, auth_client, enrollment):
        enrollment.status = CourseEnrollment.PAUSED
        enrollment.save()
        url = reverse("enrollment-resume", kwargs={"pk": enrollment.pk})
        response = auth_client.post(url)
        assert response.status_code == 200
        assert response.data["status"] == "active"

    def test_resume_already_active_returns_400(self, auth_client, enrollment):
        url = reverse("enrollment-resume", kwargs={"pk": enrollment.pk})
        response = auth_client.post(url)
        assert response.status_code == 400

    def test_resume_completed_returns_400(self, auth_client, enrollment):
        enrollment.status = CourseEnrollment.COMPLETED
        enrollment.save()
        url = reverse("enrollment-resume", kwargs={"pk": enrollment.pk})
        response = auth_client.post(url)
        assert response.status_code == 400


@pytest.mark.django_db
class TestEnrollmentResponseShape:
    def test_response_fields(self, auth_client, enrollment):
        url = reverse("enrollment-detail", kwargs={"pk": enrollment.pk})
        response = auth_client.get(url)
        data = response.data
        expected_fields = {
            "id",
            "course",
            "status",
            "progress_percent",
            "current_lesson_id",
            "started_at",
            "completed_at",
            "last_activity_at",
        }
        assert set(data.keys()) == expected_fields

    def test_nested_course_shape(self, auth_client, enrollment):
        url = reverse("enrollment-detail", kwargs={"pk": enrollment.pk})
        response = auth_client.get(url)
        course_data = response.data["course"]
        assert set(course_data.keys()) == {"id", "slug", "title"}


@pytest.mark.django_db
class TestEnrollmentProgress:
    def test_zero_progress_no_assignments(self, auth_client, enrollment):
        url = reverse("enrollment-detail", kwargs={"pk": enrollment.pk})
        response = auth_client.get(url)
        assert response.data["progress_percent"] == 0.0
        assert response.data["current_lesson_id"] is None

    def test_progress_with_completed_assignments(
        self, auth_client, user, enrollment, course
    ):
        lesson = Lesson.objects.create(
            course=course,
            title="L1",
            order=1,
            is_active=True,
        )
        a1 = Assignment.objects.create(
            lesson=lesson,
            title="A1",
            text_content="t",
            order=1,
            is_active=True,
        )
        Assignment.objects.create(
            lesson=lesson,
            title="A2",
            text_content="t",
            order=2,
            is_active=True,
        )
        CompletedAssignment.objects.create(
            user=user, assignment=a1, duration=60
        )
        url = reverse("enrollment-detail", kwargs={"pk": enrollment.pk})
        response = auth_client.get(url)
        assert response.data["progress_percent"] == 50.0
        assert response.data["current_lesson_id"] == lesson.id

    def test_current_lesson_id_points_to_first_incomplete(
        self, auth_client, user, enrollment, course
    ):
        lesson1 = Lesson.objects.create(
            course=course,
            title="L1",
            order=1,
            is_active=True,
        )
        lesson2 = Lesson.objects.create(
            course=course,
            title="L2",
            order=2,
            is_active=True,
        )
        a1 = Assignment.objects.create(
            lesson=lesson1,
            title="A1",
            text_content="t",
            order=1,
            is_active=True,
        )
        Assignment.objects.create(
            lesson=lesson2,
            title="A2",
            text_content="t",
            order=1,
            is_active=True,
        )
        CompletedAssignment.objects.create(
            user=user, assignment=a1, duration=60
        )
        url = reverse("enrollment-detail", kwargs={"pk": enrollment.pk})
        response = auth_client.get(url)
        assert response.data["current_lesson_id"] == lesson2.id

    def test_current_lesson_none_when_all_complete(
        self, auth_client, user, enrollment, course
    ):
        lesson = Lesson.objects.create(
            course=course,
            title="L1",
            order=1,
            is_active=True,
        )
        a1 = Assignment.objects.create(
            lesson=lesson,
            title="A1",
            text_content="t",
            order=1,
            is_active=True,
        )
        CompletedAssignment.objects.create(
            user=user, assignment=a1, duration=60
        )
        url = reverse("enrollment-detail", kwargs={"pk": enrollment.pk})
        response = auth_client.get(url)
        assert response.data["progress_percent"] == 100.0
        assert response.data["current_lesson_id"] is None
