# Generated by Django 5.0.3 on 2024-03-26 19:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('league_fantasy', '0010_userdraft_score_playerscorepoint_userdraftscorepoint'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='background_colour',
            field=models.CharField(default='#000000', max_length=10),
        ),
    ]
