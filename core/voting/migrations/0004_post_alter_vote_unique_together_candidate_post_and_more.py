# Generated by Django 5.2.1 on 2025-05-13 12:35

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('voting', '0003_alter_candidate_voting'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('order', models.PositiveIntegerField(default=0, help_text='Order in which this post appears in the voting form')),
                ('voting', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='voting.voting')),
            ],
            options={
                'ordering': ['order', 'title'],
                'unique_together': {('voting', 'title')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='vote',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='candidate',
            name='post',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='candidates', to='voting.post'),
        ),
        migrations.AddField(
            model_name='vote',
            name='post',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='voting.post'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='vote',
            unique_together={('voter', 'voting', 'post')},
        ),
    ]
