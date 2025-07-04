# Generated by Django 5.2 on 2025-07-01 01:13

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_alter_activitylog_content_type_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FCMDevice",
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
                (
                    "fcm_token",
                    models.CharField(
                        help_text="Firebase Cloud Messaging device token.",
                        max_length=255,
                        unique=True,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        help_text="The user associated with this device.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="fcm_devices",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "FCM Device",
                "verbose_name_plural": "FCM Devices",
                "ordering": ["-created_at"],
            },
        ),
    ]
