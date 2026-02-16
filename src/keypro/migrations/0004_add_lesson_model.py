import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


def create_lessons_from_assignments(apps, schema_editor):
    """Create one Lesson per existing Assignment, copying course/is_free/order."""
    Assignment = apps.get_model("keypro", "Assignment")
    Lesson = apps.get_model("keypro", "Lesson")

    for assignment in Assignment.objects.all():
        lesson = Lesson.objects.create(
            course=assignment.course,
            title=assignment.title,
            description=assignment.description,
            order=assignment.order,
            is_free=assignment.is_free,
            is_active=assignment.is_active,
            created_at=assignment.created_at,
        )
        assignment.lesson = lesson
        assignment.save(update_fields=["lesson"])


def reverse_lessons_to_assignments(apps, schema_editor):
    """Reverse: copy lesson data back to assignment fields."""
    Assignment = apps.get_model("keypro", "Assignment")

    for assignment in Assignment.objects.select_related("lesson").all():
        assignment.course = assignment.lesson.course
        assignment.is_free = assignment.lesson.is_free
        assignment.save(update_fields=["course", "is_free"])


class Migration(migrations.Migration):

    dependencies = [
        ("keypro", "0003_rename_lesson_to_assignment"),
    ]

    operations = [
        # 1. Create the Lesson model
        migrations.CreateModel(
            name="Lesson",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("order", models.PositiveIntegerField(default=0)),
                ("is_free", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                    ),
                ),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lessons",
                        to="keypro.course",
                    ),
                ),
            ],
            options={
                "db_table": "lesson",
                "ordering": ("order",),
            },
        ),
        # 2. Add nullable lesson FK to Assignment
        migrations.AddField(
            model_name="assignment",
            name="lesson",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="assignments",
                to="keypro.lesson",
            ),
        ),
        # 3. Data migration: create Lesson for each Assignment
        migrations.RunPython(
            create_lessons_from_assignments,
            reverse_lessons_to_assignments,
        ),
        # 4. Drop old unique_together on Assignment before removing course FK
        migrations.AlterUniqueTogether(
            name="assignment",
            unique_together=set(),
        ),
        # 5. Make lesson FK non-nullable
        migrations.AlterField(
            model_name="assignment",
            name="lesson",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="assignments",
                to="keypro.lesson",
            ),
        ),
        # 6. Remove the old course FK from Assignment
        migrations.RemoveField(
            model_name="assignment",
            name="course",
        ),
        # 7. Remove is_free from Assignment
        migrations.RemoveField(
            model_name="assignment",
            name="is_free",
        ),
        # 8. Add new unique_together on Assignment (lesson, order)
        migrations.AlterUniqueTogether(
            name="assignment",
            unique_together={("lesson", "order")},
        ),
        # 9. Add unique_together on Lesson (course, order)
        migrations.AlterUniqueTogether(
            name="lesson",
            unique_together={("course", "order")},
        ),
        # 10. Switch created_at from default to auto_now_add
        migrations.AlterField(
            model_name="lesson",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
