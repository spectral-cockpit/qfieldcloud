# Generated by Django 2.2.17 on 2020-12-01 12:09

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20201127_1256'),
    ]

    operations = [
        migrations.CreateModel(
            name='Delta',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('deltafile_id', models.UUIDField()),
                ('content', django.contrib.postgres.fields.jsonb.JSONField()),
                ('status', models.PositiveSmallIntegerField(choices=[(1, 'STATUS_PENDING'), (2, 'STATUS_BUSY'), (3, 'STATUS_APPLIED'), (4, 'STATUS_APPLIED_WITH_CONFLICTS'), (5, 'STATUS_NOT_APPLIED'), (6, 'STATUS_ERROR')], default=1)),
                ('output', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deltas', to='core.Project')),
            ],
        ),
        migrations.DeleteModel(
            name='Deltafile',
        ),
    ]
