# Generated by Django 5.0.3 on 2024-04-23 23:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('league_fantasy', '0021_playertournamentscore_cost'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='country',
            field=models.CharField(default='none', max_length=70),
        ),
    ]