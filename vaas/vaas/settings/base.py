# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
import json

import os
import environ

from vaas.configuration.loader import YamlConfigLoader


env = environ.Env()


def serialize(value: any) -> str:
    if type(value) in (dict, list, tuple):
        return json.dumps(value)
    return str(value)


config_loader = YamlConfigLoader(['/configuration'])
if config_loader.determine_config_file('config.yaml'):
    # Here we create environments variables from configuration repository and ensure that we have uppercase naming
    os.environ.update({k.upper(): serialize(v) for k, v in config_loader.get_config_tree('config.yaml').items()})

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
current_dir = os.path.abspath(os.path.dirname(__file__))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('SECRET_KEY', default='notproductionsecret')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=False)
TEMPLATE_DEBUG = env.bool('TEMPLATE_DEBUG', default=False)

# SECURITY WARNING: don't run with debug turned on in production!
ALLOWED_HOSTS = env.json('ALLOWED_HOSTS', default=[])

MESSAGE_STORAGE = env.str('MESSAGE_STORAGE', default='django.contrib.messages.storage.session.SessionStorage')

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

SOCIAL_AUTH_LOGIN_REDIRECT_URL = env.str('SOCIAL_AUTH_LOGIN_REDIRECT_URL', default='/admin/')

SECURE_CONTENT_TYPE_NOSNIFF = env.bool('SECURE_CONTENT_TYPE_NOSNIFF', default=True)

ROOT_URLCONF = env.str('ROOT_URLCONF', default='vaas.urls')

WSGI_APPLICATION = env.str('WSGI_APPLICATION', default='vaas.external.wsgi.application')

SIGNALS = env.str('SIGNALS', default='on')

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Warsaw'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = env.str('STATIC_URL', default='/static/')
STATIC_ROOT = os.path.join(BASE_DIR, "static/")

DATABASES = env.json('DATABASES', default={
    'default': {
        'ENGINE': 'vaas.db',
        'NAME': 'vaas',
        'USER': 'root',
        'PASSWORD': 'password',
        'HOST': 'mysql'
    }})

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
            'formatter': env.str('CONSOLE_LOG_FORMATTER', default='verbose'),
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

VAAS_LOADER_PARTIAL_RELOAD = env.bool('VAAS_LOADER_PARTIAL_RELOAD', default=False)
VAAS_LOADER_MAX_WORKERS = env.int('VAAS_LOADER_MAX_WORKERS', default=30)
VAAS_RENDERER_MAX_WORKERS = env.int('VAAS_RENDERER_MAX_WORKERS', default=30)
VAAS_GATHER_STATUSES_MAX_WORKERS = env.int('VAAS_GATHER_STATUSES_MAX_WORKERS', default=50)
VAAS_GATHER_STATUSES_CONNECT_TIMEOUT = env.float('VAAS_GATHER_STATUSES_CONNECT_TIMEOUT', default=0.1)

REFRESH_TRIGGERS_CLASS = tuple(env.json('REFRESH_TRIGGERS_CLASS', default=(
    'Probe', 'Backend', 'Director', 'VarnishServer', 'VclTemplate', 'VclTemplateBlock', 'TimeProfile', 'VclVariable',
    'Route'
)))

CELERY_TASK_RESULT_EXPIRES = env.int('CELERY_TASK_RESULT_EXPIRES', default=600)
CELERY_TASK_SERIALIZER = env.str('CELERY_TASK_SERIALIZER', default='json')
CELERY_RESULT_SERIALIZER = env.str('CELERY_RESULT_SERIALIZER', default='json')
CELERY_IGNORE_RESULT = env.bool('CELERY_IGNORE_RESULT', default=False)
CELERY_TASK_PUBLISH_RETRY = env.bool('CELERY_TASK_PUBLISH_RETRY', default=True)

# 5min we will wait for kill task
CELERY_TASK_SOFT_TIME_LIMIT_SECONDS = env.int('CELERY_TASK_SOFT_TIME_LIMIT_SECONDS', default=300)

CELERY_ROUTES = {
    'vaas.router.report.fetch_urls_async': {'queue': 'routes_test_queue'},
    'vaas.monitor.tasks.refresh_backend_statuses': {'queue': 'cron_queue'},
    'vaas.*': {'queue': 'worker_queue'},
}

BACKEND_STATUSES_UPDATE_INTERVAL_SECONDS = env.int('BACKEND_STATUSES_UPDATE_INTERVAL_SECONDS', default=120)

VARNISH_COMMAND_TIMEOUT = env.int('VARNISH_COMMAND_TIMEOUT', default=5)
VARNISH_VCL_INLINE_COMMAND_TIMEOUT = env.int('VARNISH_VCL_INLINE_COMMAND_TIMEOUT', default=60)

# UWSGI CONTEXT SWITCH (UGREEN)
ENABLE_UWSGI_SWITCH_CONTEXT = env.bool('ENABLE_UWSGI_SWITCH_CONTEXT', default=False)

VCL_TEMPLATE_COMMENT_REGEX = env.str('VCL_TEMPLATE_COMMENT_REGEX', default=None)
VCL_TEMPLATE_COMMENT_VALIDATION_MESSAGE = env.str('VCL_TEMPLATE_COMMENT_VALIDATION_MESSAGE', default=None)

DEFAULT_VCL_VARIABLES = env.json('DEFAULT_VCL_VARIABLES', default={
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
MESH_X_ORIGINAL_HOST = env.str('MESH_X_ORIGINAL_HOST', default='x-original-host')
SERVICE_TAG_HEADER = env.str('SERVICE_TAG_HEADER', default='x-service-tag')

if env.str('BROKER_URL_BASE', default='') and env.str('CELERY_RESULT_BACKEND_BASE', default=''):
    BROKER_URL = env.str('BROKER_URL_BASE', default='redis://redis:6379/1')
    CELERY_RESULT_BACKEND = env.str('CELERY_RESULT_BACKEND_BASE', default='redis://redis:6379/2')
else:
    BROKER_URL = 'redis://redis:6379/1'
    CELERY_RESULT_BACKEND = 'redis://redis:6379/2'


ROUTES_LEFT_CONDITIONS = env.json('ROUTES_LEFT_CONDITIONS', default={
    'req_url': 'URL_default',
    'req_http_Host': 'Domain_default',
    'req_http_X-Example': 'X-Example_default',
})
