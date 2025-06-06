# Generated by Django 5.2.1 on 2025-05-12 18:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='face_samples_count',
            field=models.PositiveSmallIntegerField(default=0, help_text='Number of face samples registered for this user'),
        ),
        migrations.AddField(
            model_name='user',
            name='has_face_data',
            field=models.BooleanField(default=False, help_text='Whether the user has facial recognition data registered'),
        ),
    ]
