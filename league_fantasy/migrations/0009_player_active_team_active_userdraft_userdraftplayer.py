# Generated by Django 5.0.3 on 2024-03-26 15:34

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('league_fantasy', '0008_game_winner'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='team',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.CreateModel(
            name='UserDraft',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserDraftPlayer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('draft', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='league_fantasy.userdraft')),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='league_fantasy.player')),
            ],
        ),
    ]
