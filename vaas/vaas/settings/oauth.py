# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from .base import env

API_ALLOW_ALL = env.bool('API_ALLOW_ALL', default=False)
API_OAUTH_ENABLED = env.bool('API_OAUTH_ENABLED', default=False)
AUDIT_BULK_OPERATIONS = env.json('AUDIT_BULK_OPERATIONS', default={})
AUTHENTICATION_BACKENDS = tuple(env.json('AUTHENTICATION_BACKENDS', default=[]))
OAUTH_AUTH_MODULE = env.str('OAUTH_AUTH_MODULE', default=None)
SOCIAL_AUTH_PIPELINE = tuple(env.json('SOCIAL_AUTH_PIPELINE', default=[]))
