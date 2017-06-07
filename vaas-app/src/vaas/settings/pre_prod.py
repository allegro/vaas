# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from .base import *

from vaas.configuration.loader import YamlConfigLoader

DEBUG = True
TEMPLATE_DEBUG = True

for key, value in YamlConfigLoader().get_config_tree('pre_prod.yml').iteritems():
    globals()[key] = value

INSTALLED_APPS = INSTALLED_APPS + tuple(INSTALLED_PLUGINS)
MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + tuple(MIDDLEWARE_PLUGINS)
