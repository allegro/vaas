# Generated by Django 3.1.14 on 2022-02-09 07:22

from django.db import migrations, models
import vaas.manager.fields


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0008_auto_20211027_1421'),
    ]

    operations = [
        migrations.AddField(
            model_name='timeprofile',
            name='service_mesh_timeout',
            field=vaas.manager.fields.NormalizedDecimalField(decimal_places=2, default='300', max_digits=5, verbose_name='Service mesh timeout (s)'),
        ),
        migrations.AlterField(
            model_name='director',
            name='reachable_via_service_mesh',
            field=models.BooleanField(default=False, help_text='<i>Pass traffic to backends via service mesh if varnish cluster supports it</i>'),
        ),
    ]
