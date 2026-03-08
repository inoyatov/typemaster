from django.urls import path

from keypro.views import (
    CourseEnrollmentDetailView,
    CourseEnrollView,
    CourseListView,
    EnrollmentCancelView,
    EnrollmentDetailView,
    EnrollmentListView,
    EnrollmentResumeView,
    LessonDetailView,
    LessonListView,
)

urlpatterns = [
    path("courses/", CourseListView.as_view(), name="course-list"),
    path(
        "courses/<slug:course_slug>/lessons/",
        LessonListView.as_view(),
        name="lesson-list",
    ),
    path(
        "courses/<slug:course_slug>/lessons/<int:pk>/",
        LessonDetailView.as_view(),
        name="lesson-detail",
    ),
    path(
        "enrollments/",
        EnrollmentListView.as_view(),
        name="enrollment-list",
    ),
    path(
        "enrollments/<int:pk>/",
        EnrollmentDetailView.as_view(),
        name="enrollment-detail",
    ),
    path(
        "enrollments/<int:pk>/cancel/",
        EnrollmentCancelView.as_view(),
        name="enrollment-cancel",
    ),
    path(
        "enrollments/<int:pk>/resume/",
        EnrollmentResumeView.as_view(),
        name="enrollment-resume",
    ),
    path(
        "courses/<int:course_id>/enroll/",
        CourseEnrollView.as_view(),
        name="course-enroll",
    ),
    path(
        "courses/<int:course_id>/enrollment/",
        CourseEnrollmentDetailView.as_view(),
        name="course-enrollment-detail",
    ),
]
