# Generated by Django 5.0.3 on 2024-04-06 19:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('league_fantasy', '0018_gameplayer_team'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='region',
            field=models.CharField(default='Europe', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='tournament',
            name='disambig_name',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
    ]