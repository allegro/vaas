# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from .base import *

from vaas.configuration.loader import YamlConfigLoader

DEBUG = True
TEMPLATE_DEBUG = True

for key, value in YamlConfigLoader().get_config_tree('pre_prod.yml').items():
    globals()[key] = value

INSTALLED_APPS = tuple(INSTALLED_PLUGINS) + INSTALLED_APPS
MIDDLEWARE = MIDDLEWARE + list(MIDDLEWARE_PLUGINS)

from .oauth import *
