# Generated by Django 2.2.17 on 2021-01-18 16:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0013_remove_exportation_output"),
    ]

    operations = [
        migrations.AddField(
            model_name="exportation",
            name="output",
            field=models.TextField(null=True),
        ),
    ]
