# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from .base import *

DEBUG = True
TEMPLATE_DEBUG = True

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

NOSE_ARGS = [
    '--exclude-dir=' + os.path.abspath(os.path.dirname(__file__) + '/'), '--with-xunit'
]
