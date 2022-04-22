# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from .base import *

AUTHENTICATION_BACKENDS = tuple(env.json('AUTHENTICATION_BACKENDS', default=[]))
SOCIAL_AUTH_PIPELINE = tuple(env.json('SOCIAL_AUTH_PIPELINE', default=[]))
