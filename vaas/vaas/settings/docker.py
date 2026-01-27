# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from .base import *

DEBUG = True
TEMPLATE_DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = tuple(INSTALLED_PLUGINS) + INSTALLED_APPS
MIDDLEWARE = MIDDLEWARE + list(env.json('MIDDLEWARE_PLUGINS', default=[]))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        "json": {
            "()": "vaas.settings.logger.CustomJsonFormatter",
            "fmt": "%(levelname)s %(asctime)s %(name)s %(module)s %(message)s",
            "rename_fields": {
                "levelname": "level",
                "asctime": "@timestamp",
            },
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/tmp/debug.log',
            'formatter': env.str('CONSOLE_LOG_FORMATTER', default='verbose')
        },
        'console': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': env.str('CONSOLE_LOG_FORMATTER', default='verbose'),
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
