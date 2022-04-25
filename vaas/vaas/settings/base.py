# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import os
import environ
from django.conf import global_settings
from django.contrib import messages

from vaas.configuration.loader import YamlConfigLoader


env = environ.Env()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
current_dir = os.path.abspath(os.path.dirname(__file__))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'notproductionsecret'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: don't run with debug turned on in production!
ALLOWED_HOSTS = []

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# Application definition
INSTALLED_APPS = (
    'django_nose',
    'vaas.adminext',
    'django_admin_bootstrapped',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'social_django',
    'tastypie',
    'vaas.manager',
    'vaas.cluster',
    'vaas.router',
    'vaas.monitor',
    'vaas.account',
    'vaas.purger',
    'taggit',
    'django_ace',
    'simple_history',
    'django_celery_beat',
)

# Plugins definition
INSTALLED_PLUGINS = ()
MIDDLEWARE_PLUGINS = ()

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'log_request_id.middleware.RequestIDMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'vaas.manager.middleware.VclRefreshMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/admin/'

SECURE_CONTENT_TYPE_NOSNIFF = True

ROOT_URLCONF = 'vaas.urls'

WSGI_APPLICATION = 'vaas.external.wsgi.application'

SIGNALS = 'on'

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Warsaw'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static/")

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'), ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.i18n',
                'django.template.context_processors.debug',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.request',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'fmt': '%(levelname)s %(asctime)s %(name)s %(module)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': False,
            'level': 'ERROR',
        },
        'vaas': {
            'handlers': ['console'],
            'propagate': False,
            'level': 'DEBUG',
        },
        'celery': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        '': {
            'handlers': ['console'],
            'level': 'INFO',
        }
    }
}

VAAS_LOADER_MAX_WORKERS = 30
VAAS_RENDERER_MAX_WORKERS = 30
VAAS_GATHER_STATUSES_MAX_WORKERS = 50
VAAS_GATHER_STATUSES_CONNECT_TIMEOUT = 0.1

REFRESH_TRIGGERS_CLASS = (
    'Probe', 'Backend', 'Director', 'VarnishServer', 'VclTemplate', 'VclTemplateBlock', 'TimeProfile', 'VclVariable',
    'Route'
)

CELERY_TASK_RESULT_EXPIRES = env.int('CELERY_TASK_RESULT_EXPIRES', default=600)
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_IGNORE_RESULT = env.bool('CELERY_IGNORE_RESULT', False)
CELERY_TASK_PUBLISH_RETRY = env.bool('CELERY_TASK_PUBLISH_RETRY', True)

# 5min we will wait for kill task
CELERY_TASK_SOFT_TIME_LIMIT_SECONDS = 300

CELERY_ROUTES = {
    'vaas.router.report.fetch_urls_async': {'queue': 'routes_test_queue'},
    'vaas.monitor.tasks.refresh_backend_statuses': {'queue': 'cron_queue'},
    'vaas.*': {'queue': 'worker_queue'},
}

BACKEND_STATUSES_UPDATE_INTERVAL_SECONDS = 120

VARNISH_COMMAND_TIMEOUT = 5
VARNISH_VCL_INLINE_COMMAND_TIMEOUT = 60

# UWSGI CONTEXT SWITCH (UGREEN)
ENABLE_UWSGI_SWITCH_CONTEXT = env.bool('ENABLE_UWSGI_SWITCH_CONTEXT', False)

VCL_TEMPLATE_COMMENT_REGEX = env.str('VCL_TEMPLATE_COMMENT_REGEX', default=None)
VCL_TEMPLATE_COMMENT_VALIDATION_MESSAGE = env.str('VCL_TEMPLATE_COMMENT_VALIDATION_MESSAGE', default=None)

DEFAULT_VCL_VARIABLES = env.dict('DEFAULT_VCL_VARIABLES', default={
    'MESH_IP': '127.0.0.1',
    'MESH_PORT': '31001',
    'MESH_TIMEOUT_CONTROL_HEADER': 'x-service-mesh-timeout',
})

PURGER_HTTP_CLIENT_TIMEOUT = env.int('PURGER_HTTP_CLIENT_TIMEOUT', default=10)
PURGER_MAX_HTTP_WORKERS = env.int('PURGER_MAX_HTTP_WORKERS', default=100)

# VALIDATION_HEADER
VALIDATION_HEADER = env.str('VALIDATION_HEADER', default='x-validation')

FETCHER_HTTP_CLIENT_TIMEOUT = env.int('FETCHER_HTTP_CLIENT_TIMEOUT', default=10)
FETCHER_MAX_HTTP_WORKERS = env.int('FETCHER_MAX_HTTP_WORKERS', default=100)

# ENABLE RUN TEST BUTTON
ROUTE_TESTS_ENABLED = env.bool('ROUTE_TESTS_ENABLED', default=True)

# STATSD ENV
STATSD_ENABLE = env.bool('STATSD_ENABLE', default=False)
STATSD_HOST = env.str('STATSD_HOST', default='localhost')
STATSD_PORT = env.int('STATSD_PORT', default=8125)
STATSD_PREFIX = env.str('STATSD_PREFIX', default='example.statsd.path')

# HEADER FOR PERMIT ACCESS TO /vaas/ ENDPOINT
ALLOW_METRICS_HEADER = env.bool('ALLOW_METRICS_HEADER', default='x-allow-metric-header')

CLUSTER_IN_SYNC_ENABLED = env.bool('CLUSTER_IN_SYNC_ENABLED', default=False)
MESH_X_ORIGINAL_HOST = env.bool('MESH_X_ORIGINAL_HOST', default='x-original-host')
SERVICE_TAG_HEADER = env.bool('SERVICE_TAG_HEADER', default='x-service-tag')

for key, value in YamlConfigLoader(['/configuration']).get_config_tree('config.yaml').items():
    globals()[key.upper()] = value

if 'BROKER_URL_BASE' in globals():
    BROKER_URL = BROKER_URL_BASE
    CELERY_RESULT_BACKEND = CELERY_RESULT_BACKEND_BASE
else:
    BROKER_URL = 'redis://redis:6379/1'
    CELERY_RESULT_BACKEND = 'redis://redis:6379/2'

if 'CONSOLE_LOG_FORMATTER' in globals():
    LOGGING['handlers']['console']['formatter'] = CONSOLE_LOG_FORMATTER

ROUTES_LEFT_CONDITIONS = {}
if 'ROUTES_LEFT_CONDITIONS_BASE' in globals():
    for condition in ROUTES_LEFT_CONDITIONS_BASE:
        ROUTES_LEFT_CONDITIONS[condition['name']] = condition['value']
else:
    ROUTES_LEFT_CONDITIONS = env.dict('ROUTES_LEFT_CONDITIONS', default={
        'req_url': 'URL_default',
        'req_http_Host': 'Domain_default',
        'req_http_X-Example': 'X-Example_default',
    })

SENTRY_DSN = env.str('SENTRY_DSN', default='')