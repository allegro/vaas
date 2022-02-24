# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from .base import *

from vaas.configuration.loader import YamlConfigLoader

DEBUG = True
TEMPLATE_DEBUG = True

for key, value in YamlConfigLoader(['/configuration']).get_config_tree('config.yaml').items():
    globals()[key.upper()] = value

INSTALLED_APPS = tuple(INSTALLED_PLUGINS) + INSTALLED_APPS
MIDDLEWARE = MIDDLEWARE + list(MIDDLEWARE_PLUGINS)

from .oauth import *
from .tracking import *
