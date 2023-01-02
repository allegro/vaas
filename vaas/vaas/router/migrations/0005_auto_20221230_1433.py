# Generated by Django 3.1.14 on 2022-12-30 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('router', '0004_redirect_rewrite_groups'),
    ]

    operations = [
        migrations.AddField(
            model_name='redirect',
            name='required_custom_header',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='redirect',
            name='destination',
            field=models.CharField(max_length=512),
        ),
    ]