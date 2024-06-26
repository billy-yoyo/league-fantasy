# Generated by Django 5.0.3 on 2024-03-26 10:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('league_fantasy', '0005_tournament_alter_game_tournament'),
    ]

    operations = [
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='tournament',
            name='season',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, to='league_fantasy.season'),
            preserve_default=False,
        ),
    ]
