# Generated by Django 3.1.8 on 2021-05-26 11:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0004_auto_20210519_1334'),
    ]

    operations = [
        migrations.AddField(
            model_name='director',
            name='service_mesh_label',
            field=models.CharField(default='', max_length=128),
        ),
    ]
