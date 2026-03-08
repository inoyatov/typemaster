from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

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
    is_free = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("order",)
        db_table = "lesson"
        unique_together = (("course", "order"),)

    def __str__(self):
        return self.title


class Assignment(models.Model):
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="assignments"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    text_content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("order",)
        db_table = "assignment"
        unique_together = (("lesson", "order"),)

    def __str__(self):
        return self.title


class CourseEnrollment(models.Model):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELED = "canceled"
    STATUS_CHOICES = [
        (ACTIVE, "Active"),
        (COMPLETED, "Completed"),
        (PAUSED, "Paused"),
        (CANCELED, "Canceled"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="enrollments"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="enrollments"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=ACTIVE
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_activity_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "course_enrollment"
        ordering = ("-enrolled_at",)
        unique_together = (("user", "course"),)

    def __str__(self):
        return f"{self.user} — {self.course}"


class CompletedAssignment(models.Model):
    class ActionType(models.TextChoices):
        COMPLETE = "complete", "Complete"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="completed_assignments",
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="completions",
    )
    action_type = models.CharField(
        max_length=20,
        choices=ActionType.choices,
        default=ActionType.COMPLETE,
    )
    average_speed = models.PositiveIntegerField(
        help_text="Average typing speed (chars/min)",
        default=0,
    )
    mistakes_count = models.PositiveIntegerField(
        default=0,
    )
    completed_at = models.DateTimeField(
        default=timezone.now,
    )

    class Meta:
        db_table = "completed_assignment"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "assignment"],
                name="unique_user_assignment_completion",
            ),
        ]

    def __str__(self):
        return f"{self.user} — {self.assignment}"
