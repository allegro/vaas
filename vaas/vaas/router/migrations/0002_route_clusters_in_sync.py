# Generated by Django 3.1.5 on 2021-03-24 10:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('router', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='route',
            name='clusters_in_sync',
            field=models.BooleanField(default=False),
        ),
    ]
