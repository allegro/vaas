# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from vaas.configuration.loader import YamlConfigLoader

for key, value in YamlConfigLoader(['/configuration']).get_config_tree('config.yaml').items():
    globals()[key.upper()] = value

AUTHENTICATION_BACKENDS = tuple(AUTHENTICATION_BACKENDS)
SOCIAL_AUTH_PIPELINE = tuple(SOCIAL_AUTH_PIPELINE)
