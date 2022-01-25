# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from .base import *

from vaas.configuration.loader import YamlConfigLoader

DEBUG = True
TEMPLATE_DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = tuple(INSTALLED_PLUGINS) + INSTALLED_APPS
MIDDLEWARE = MIDDLEWARE + list(MIDDLEWARE_PLUGINS)

for key, value in YamlConfigLoader(['/configuration']).get_config_tree('docker.yaml').items():
    globals()[key.upper()] = value

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/db/db.sqlite3',
    }
}
