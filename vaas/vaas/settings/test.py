# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from .base import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/db.sqlite3',
    }
}

TEST_RUNNER = 'django.test.runner.DiscoverRunner'
