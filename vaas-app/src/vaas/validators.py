# -*- coding: utf-8 -*-

import re

from django.core.validators import RegexValidator, ValidationError
from django.conf import settings

vcl_name_re = re.compile(r'^[a-zA-Z0-9_]+$')
vcl_name_validator = RegexValidator(vcl_name_re, "Allowed characters: letters, numbers and underscores.", 'invalid')

vcl_dc_name_re = re.compile(r'^[a-zA-Z0-9]+$')
vcl_dc_name_validator = RegexValidator(vcl_dc_name_re, "Allowed characters: letters and numbers", 'invalid')

vcl_variable_key_re = re.compile(r'^\w+$')
vcl_variable_key_validator = RegexValidator(vcl_variable_key_re, "Characters must match '^\w+$' regex.", 'invalid')

vcl_template_comment_validator = RegexValidator(regex=settings.VCL_TEMPLATE_COMMENT_REGEX,
                                                message=settings.VCL_TEMPLATE_COMMENT_VALIDATION_MESSAGE)


class VclVariableValidatorError(ValidationError):
    pass


def vcl_variable_validator(vcl_content, vcl_pk, vcl_variable_class, varnish_server_class):

    pattern = re.compile('#{\w+}', re.MULTILINE)
    placeholders = re.findall(pattern, vcl_content)
    placeholders = {p[2:-1] for p in placeholders}
    vcl_clusters = {server.cluster.pk for server in varnish_server_class.objects.all() if server.template.pk == vcl_pk}
    if placeholders and vcl_clusters:
        variables = list(vcl_variable_class.objects.filter(cluster__in=vcl_clusters))
        keys = {variable.key for variable in variables}
        missing_variables = ', '.join(placeholders - keys)
        if missing_variables:
            raise VclVariableValidatorError('Undefined variables detected: {}'.format(missing_variables))
