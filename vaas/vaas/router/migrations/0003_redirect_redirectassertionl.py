# Generated by Django 3.1.14 on 2022-11-21 09:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('router', '0002_route_clusters_in_sync'),
    ]

    operations = [
        migrations.CreateModel(
            name='Redirect',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('condition', models.CharField(max_length=512)),
                ('destination', models.CharField(max_length=512)),
                ('action',
                 models.IntegerField(choices=[(301, 'Move Permanently'), (302, 'Found'), (307, 'Temporary Redirect')],
                                     default=301)),
                ('priority', models.PositiveIntegerField()),
                ('preserve_query_params', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='RedirectAssertion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('given_url', models.URLField()),
                ('expected_location', models.CharField(max_length=512)),
                ('redirect', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assertions',
                                               related_query_name='redirect_assertions', to='router.redirect')),
            ],
        ),
    ]