# Generated by Django 5.0.3 on 2025-02-08 14:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('league_fantasy', '0023_player_overview_page'),
    ]

    operations = [
        migrations.AddField(
            model_name='userdraft',
            name='score_offset',
            field=models.FloatField(default=0),
        ),
    ]
