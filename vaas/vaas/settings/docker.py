# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from .base import *

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
            'formatter': env.str('CONSOLE_LOG_FORMATTER', default='verbose')
        },
        'console': {
            'class': 'logging.StreamHandler',
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
