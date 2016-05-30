# -*- coding: utf-8 -*-

import re

from django.core.validators import RegexValidator

vcl_name_re = re.compile(r'^[a-zA-Z0-9_]+$')
vcl_name_validator = RegexValidator(vcl_name_re, "Allowed characters: letters, numbers and underscores.", 'invalid')
