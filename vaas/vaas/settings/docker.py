# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from .base import *

from vaas.configuration.loader import YamlConfigLoader

DEBUG = True
TEMPLATE_DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = tuple(INSTALLED_PLUGINS) + INSTALLED_APPS
MIDDLEWARE = MIDDLEWARE + list(MIDDLEWARE_PLUGINS)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/tmp/debug.log',
            'formatter': 'verbose'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'propagate': False,
            'level': 'ERROR',
        },
        'vaas': {
            'handlers': ['file', 'console'],
            'propagate': False,
            'level': 'DEBUG',
        },
        '': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
        }
    }
}

for key, value in YamlConfigLoader(['/configuration']).get_config_tree('docker.yaml').items():
    globals()[key.upper()] = value

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'vaas',
        'USER': 'root',
        'PASSWORD': 'password',
        'HOST': 'mysql',
        'OPTIONS': {
            'init_command': "SET GLOBAL sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''));"
        }
    }
}
