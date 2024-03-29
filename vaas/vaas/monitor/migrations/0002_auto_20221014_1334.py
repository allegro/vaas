# Generated by Django 3.1.14 on 2022-10-14 11:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='backendstatus',
            name='backend_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='backendstatus',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='backendstatus',
            name='address',
        ),
        migrations.RemoveField(
            model_name='backendstatus',
            name='port',
        ),
    ]
