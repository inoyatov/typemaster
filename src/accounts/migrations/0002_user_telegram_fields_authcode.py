# Generated manually

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="telegram_chat_id",
            field=models.BigIntegerField(
                blank=True,
                null=True,
                unique=True,
                verbose_name="telegram chat ID",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="telegram_username",
            field=models.CharField(
                blank=True,
                max_length=150,
                null=True,
                unique=True,
                verbose_name="telegram username",
            ),
        ),
        migrations.CreateModel(
            name="AuthCode",
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
                ("code", models.CharField(db_index=True, max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "auth_code",
                "ordering": ("-created_at",),
            },
        ),
    ]
