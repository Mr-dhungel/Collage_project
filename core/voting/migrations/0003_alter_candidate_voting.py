# Generated by Django 5.2.1 on 2025-05-13 11:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0002_candidate_photo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidate',
            name='voting',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='candidates', to='voting.voting'),
        ),
    ]
