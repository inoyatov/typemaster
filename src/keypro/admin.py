from django.contrib import admin

from .models import Assignment, Course, Lesson


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_active", "order")
    list_filter = ("is_active",)
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order", "is_free", "is_active")
    list_filter = ("is_free", "is_active", "course")
    search_fields = ("title",)


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson", "order", "is_active")
    list_filter = ("is_active", "lesson__course")
    search_fields = ("title",)
