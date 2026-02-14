from django.urls import path

from keypro.views import CourseListView, LessonDetailView, LessonListView

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
]
