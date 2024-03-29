# Generated by Django 3.1.5 on 2021-01-21 11:37

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import re
import simple_history.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Dc',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('symbol', models.CharField(max_length=9, unique=True, validators=[
                    django.core.validators.RegexValidator(re.compile('^[a-zA-Z0-9_]+$'),
                                                          'Allowed characters: letters, numbers and underscores.',
                                                          'invalid')])),
            ],
        ),
        migrations.CreateModel(
            name='LogicalCluster',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, validators=[
                    django.core.validators.RegexValidator(re.compile('^[a-zA-Z0-9_]+$'),
                                                          'Allowed characters: letters, numbers and underscores.',
                                                          'invalid')])),
                ('reload_timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('error_timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_error_info', models.CharField(blank=True, max_length=400, null=True)),
                ('current_vcl_versions', models.CharField(default='[]', max_length=400)),
            ],
        ),
        migrations.CreateModel(
            name='VclTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, validators=[
                    django.core.validators.RegexValidator(re.compile('^[a-zA-Z0-9_]+$'),
                                                          'Allowed characters: letters, numbers and underscores.',
                                                          'invalid')])),
                ('content', models.TextField()),
                ('version', models.CharField(choices=[('4.0', 'Vcl 4.0')], default='4.0', max_length=3)),
                ('comment', models.CharField(max_length=64, validators=[
                    django.core.validators.RegexValidator(message=None, regex=None)])),
            ],
        ),
        migrations.CreateModel(
            name='HistoricalVclTemplateBlock',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('tag', models.CharField(choices=[
                    ('VCL', 'VCL'), ('HEADERS', 'VCL/HEADERS'), ('ACL', 'VCL/ACL'), ('BACKENDS', 'VCL/BACKENDS'),
                    ('DIRECTORS', 'VCL/DIRECTORS'), ('RECV', 'VCL/RECEIVE'), ('ROUTER', 'VCL/RECEIVE/ROUTER'),
                    ('PROPER_PROTOCOL_REDIRECT', 'RECEIVE/PROPER_PROTOCOL_REDIRECT'),
                    ('OTHER_FUNCTIONS', 'VCL/OTHER_FUNCTIONS'), ('EMPTY_DIRECTOR_SYNTH', 'VCL/EMPTY_DIRECTOR_SYNTH')],
                    max_length=100)),
                ('content', models.TextField()),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[
                    ('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                   related_name='+', to=settings.AUTH_USER_MODEL)),
                ('template', models.ForeignKey(blank=True, db_constraint=False, null=True,
                                               on_delete=django.db.models.deletion.DO_NOTHING, related_name='+',
                                               to='cluster.vcltemplate')),
            ],
            options={
                'verbose_name': 'historical vcl template block',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalVclTemplate',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=100, validators=[
                    django.core.validators.RegexValidator(re.compile('^[a-zA-Z0-9_]+$'),
                                                          'Allowed characters: letters, numbers and underscores.',
                                                          'invalid')])),
                ('content', models.TextField()),
                ('version', models.CharField(choices=[('4.0', 'Vcl 4.0')], default='4.0', max_length=3)),
                ('comment', models.CharField(max_length=64, validators=[
                    django.core.validators.RegexValidator(message=None, regex=None)])),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')],
                                                  max_length=1)),
                ('history_user', models.ForeignKey(null=True,
                                                   on_delete=django.db.models.deletion.SET_NULL,
                                                   related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical vcl template',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='VclVariable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=100, validators=[
                    django.core.validators.RegexValidator(re.compile('^\\w+$'), "Characters must match '^\\w+$' regex.",
                                                          'invalid')])),
                ('value', models.CharField(max_length=254)),
                ('cluster', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING,
                                              to='cluster.logicalcluster')),
            ],
            options={
                'unique_together': {('key', 'cluster')},
            },
        ),
        migrations.CreateModel(
            name='VclTemplateBlock',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag', models.CharField(choices=[('VCL', 'VCL'), ('HEADERS', 'VCL/HEADERS'), ('ACL', 'VCL/ACL'),
                                                  ('BACKENDS', 'VCL/BACKENDS'), ('DIRECTORS', 'VCL/DIRECTORS'),
                                                  ('RECV', 'VCL/RECEIVE'), ('ROUTER', 'VCL/RECEIVE/ROUTER'),
                                                  ('PROPER_PROTOCOL_REDIRECT', 'RECEIVE/PROPER_PROTOCOL_REDIRECT'),
                                                  ('OTHER_FUNCTIONS', 'VCL/OTHER_FUNCTIONS'),
                                                  ('EMPTY_DIRECTOR_SYNTH', 'VCL/EMPTY_DIRECTOR_SYNTH')],
                                         max_length=100)),
                ('content', models.TextField()),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='cluster.vcltemplate')),
            ],
            options={
                'unique_together': {('tag', 'template')},
            },
        ),
        migrations.CreateModel(
            name='VarnishServer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.GenericIPAddressField(protocol='IPv4')),
                ('hostname', models.CharField(max_length=50)),
                ('cluster_weight', models.PositiveIntegerField(default='1', validators=[
                    django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(100)])),
                ('http_port', models.PositiveIntegerField(default='80', validators=[
                    django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(65535)])),
                ('port', models.PositiveIntegerField(default='6082', validators=[
                    django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(65535)])),
                ('secret', models.CharField(max_length=40)),
                ('status', models.CharField(choices=[('active', 'Active'), ('maintenance', 'Maintenance'),
                                                     ('disabled', 'Disabled')], default='disabled', max_length=15)),
                ('is_canary', models.BooleanField(default=False)),
                ('cluster', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                              to='cluster.logicalcluster')),
                ('dc', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='cluster.dc')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='cluster.vcltemplate')),
            ],
            options={
                'unique_together': {('ip', 'port')},
            },
        ),
    ]
