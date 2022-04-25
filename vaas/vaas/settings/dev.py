# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from .base import *

DEBUG = True
TEMPLATE_DEBUG = True

INSTALLED_APPS = tuple(INSTALLED_PLUGINS) + INSTALLED_APPS
MIDDLEWARE = MIDDLEWARE + list(MIDDLEWARE_PLUGINS)

from .oauth import *
from .tracking import *
