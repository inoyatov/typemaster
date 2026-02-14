from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Course(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(
        upload_to=settings.DEFAULT_COURSE_PATH, blank=True
    )
    author = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("order",)
        db_table = "course"

    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="lessons"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    text_content = models.TextField()
    is_free = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("order",)
        db_table = "lesson"
        unique_together = (("course", "order"),)

    def __str__(self):
        return self.title


class CourseEnrollment(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="enrollments"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="enrollments"
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "course_enrollment"
        unique_together = (("user", "course"),)

    def __str__(self):
        return f"{self.user} — {self.course}"


class CompletedLesson(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="completed_lessons"
    )
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="completions"
    )
    duration = models.PositiveIntegerField(help_text="Time spent in seconds")
    error_count = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "completed_lesson"

    def __str__(self):
        return f"{self.user} — {self.lesson}"
