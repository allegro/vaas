# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from .base import *

DEBUG = True

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

from vaas.settings.ldap import *

from vaas.settings.oauth import *
