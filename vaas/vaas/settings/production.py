# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from .base import *

INSTALLED_APPS = tuple(INSTALLED_PLUGINS) + INSTALLED_APPS
MIDDLEWARE = MIDDLEWARE + list(MIDDLEWARE_PLUGINS)

SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

from .oauth import *
from .tracking import *
