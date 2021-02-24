# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from .base import *
from vaas.configuration.loader import YamlConfigLoader

DEBUG = False
TEMPLATE_DEBUG = False
ALLOWED_HOSTS = ["*"]

# override some configurations
for key, value in YamlConfigLoader().get_config_tree('production.yml').items():
    globals()[key] = value

INSTALLED_APPS = tuple(INSTALLED_PLUGINS) + INSTALLED_APPS
MIDDLEWARE = MIDDLEWARE + list(MIDDLEWARE_PLUGINS)

SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

from .oauth import *
