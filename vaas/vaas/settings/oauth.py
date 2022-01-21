# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from vaas.configuration.loader import YamlConfigLoader

oauth_config = YamlConfigLoader(['/configuration']).get_config_tree('oauth.yaml')
if oauth_config:
    for key, value in oauth_config.items():
        globals()[key.upper()] = value

    AUTHENTICATION_BACKENDS = tuple(AUTHENTICATION_BACKENDS)
    SOCIAL_AUTH_PIPELINE = tuple(SOCIAL_AUTH_PIPELINE)
