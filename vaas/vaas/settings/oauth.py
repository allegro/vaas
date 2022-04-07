# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from .base import *

AUTHENTICATION_BACKENDS = tuple(literal_eval(env('AUTHENTICATION_BACKENDS', default='[]')))
SOCIAL_AUTH_PIPELINE = tuple(literal_eval(env('SOCIAL_AUTH_PIPELINE', default='[]')))
