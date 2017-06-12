# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from .base import *

DEBUG = True

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

NOSE_ARGS = ['--exclude-dir=vaas/settings']

from vaas.settings.ldap import *
