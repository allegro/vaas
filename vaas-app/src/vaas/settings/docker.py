# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from .base import *

DEBUG = False
TEMPLATE_DEBUG = False
ALLOWED_HOSTS = ["*"]
STATIC_ROOT = '/home/ubuntu/static'
DATABASES = {
    'default': {
          'ENGINE': 'django.db.backends.sqlite3',
          'NAME': '/tmp/db.sqlite3',
    }
}
