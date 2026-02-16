import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("keypro", "0002_completedlesson_courseenrollment"),
    ]

    operations = [
        # 1. Rename model classes
        migrations.RenameModel(
            old_name="Lesson",
            new_name="Assignment",
        ),
        migrations.RenameModel(
            old_name="CompletedLesson",
            new_name="CompletedAssignment",
        ),
        # 2. Rename DB tables
        migrations.AlterModelTable(
            name="assignment",
            table="assignment",
        ),
        migrations.AlterModelTable(
            name="completedassignment",
            table="completed_assignment",
        ),
        # 3. Update related_name on Course FK (lessons -> assignments)
        migrations.AlterField(
            model_name="assignment",
            name="course",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="assignments",
                to="keypro.course",
            ),
        ),
        # 4. Rename FK field lesson -> assignment on CompletedAssignment
        migrations.RenameField(
            model_name="completedassignment",
            old_name="lesson",
            new_name="assignment",
        ),
        # 5. Update related_name on User FK (completed_lessons -> completed_assignments)
        migrations.AlterField(
            model_name="completedassignment",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="completed_assignments",
                to="accounts.user",
            ),
        ),
    ]
