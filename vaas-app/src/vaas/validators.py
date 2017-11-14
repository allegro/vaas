# -*- coding: utf-8 -*-

import re

from django.core.validators import RegexValidator, ValidationError
from django.conf import settings

vcl_name_re = re.compile(r'^[a-zA-Z0-9_]+$')
vcl_name_validator = RegexValidator(vcl_name_re, "Allowed characters: letters, numbers and underscores.", 'invalid')


class VclVariableValidator(ValidationError):
    pass


def vcl_variable_validator(vcl_content, vcl_pk, vcl_variable_class, varnish_server_class):

    placeholders = re.findall(settings.VCL_VARIABLE_PATTERN, vcl_content)
    placeholders = [p[2:-1] for p in placeholders]
    vcl_clusters = {server.cluster.pk for server in varnish_server_class.objects.all() if server.template.pk == vcl_pk}
    if placeholders and vcl_clusters:
        variables = list(vcl_variable_class.objects.filter(cluster__in=vcl_clusters))
        keys = [variable.key for variable in variables]
        missing_variables = ', '.join(set(placeholders) - set(keys))
        if missing_variables:
            raise VclVariableValidator('Undefined variables detected: {}'.format(missing_variables))
