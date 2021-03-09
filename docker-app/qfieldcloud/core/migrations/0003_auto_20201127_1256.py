# Generated by Django 2.2.17 on 2020-11-27 12:56

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_deltafile"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserAccount",
            fields=[
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        serialize=False,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "account_type",
                    models.PositiveSmallIntegerField(
                        choices=[(1, "community"), (2, "pro")], default=1
                    ),
                ),
                ("storage_limit_mb", models.PositiveIntegerField(default=100)),
                ("db_limit_mb", models.PositiveIntegerField(default=25)),
                (
                    "synchronizations_per_months",
                    models.PositiveIntegerField(default=30),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="deltafile",
            name="status",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (1, "STATUS_PENDING"),
                    (2, "STATUS_BUSY"),
                    (3, "STATUS_APPLIED"),
                    (4, "STATUS_APPLIED_WITH_CONFLICTS"),
                    (5, "STATUS_NOT_APPLIED"),
                    (6, "STATUS_ERROR"),
                ],
                default=1,
            ),
        ),
    ]
