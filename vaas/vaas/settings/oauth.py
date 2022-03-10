# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from .base import AUTHENTICATION_BACKENDS, SOCIAL_AUTH_PIPELINE

AUTHENTICATION_BACKENDS = tuple(AUTHENTICATION_BACKENDS)
SOCIAL_AUTH_PIPELINE = tuple(SOCIAL_AUTH_PIPELINE)
