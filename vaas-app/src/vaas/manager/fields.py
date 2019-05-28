# -*- coding: utf-8 -*-

from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.html import mark_safe


def generate_choices(min, max, step, decimal_places=2):
    format_str = "{0:." + str(decimal_places) + "f}"
    choices = [
        (Decimal(format_str.format(x / Decimal(step))), format_str.format(x / Decimal(step))) for x in range(min, max)
    ]

    return choices


def make_backend_name(backend):

    ip_octets = backend.address.split('.')
    name = "_%s_%s_%s_%s_%s" % (backend.id, backend.dc, ip_octets[2], ip_octets[3], backend.port)
    director = str(backend.director)

    if len(name) > 64:
        return name[-64:]
    elif len(name) + len(director) > 64:
        return "%s%s" % (director[0:(64 - len(name))], name)

    return "%s%s" % (director, name)


class NormalizedDecimalField(models.DecimalField):

    def to_python(self, value):
        if value is None:
            return value
        try:
            format_str = "{0:." + str(self.decimal_places) + "f}"
            return Decimal(format_str.format(float(value)))
        except:
            raise ValidationError(
                self.error_messages['invalid'],
                code='invalid',
                params={'value': value},
            )


class ConditionWidget(forms.MultiWidget):
    def __init__(self, variables, operators, *args, **kwargs):
        widgets = [
            forms.Select(choices=variables, attrs={'class': 'form-control', 'col': 'col-md-2'}),
            forms.Select(choices=operators, attrs={'class': 'form-control', 'col': 'col-md-2'}),
            forms.TextInput(attrs={'class': 'form-control', 'col': 'col-md-4'}),
        ]
        super(ConditionWidget, self).__init__(widgets, *args, **kwargs)
        self.template_name = 'forms/condition.html'

    def decompress(self, value):
        if value:
            parts = value.split(' ')
            left = parts.pop(0)
            operator = parts.pop(0)
            right = ' '.join(parts)
            if len(right) and right[0] == '"':
                right = right[1:]
            if right[-1] == '"':
                right = right[:-1]
            return left, operator, right
        return ['req.url', '~', '']

    def value_from_datadict(self, data, files, name):
        parts = super(ConditionWidget, self).value_from_datadict(data, files, name)
        parts[2] = '"{}"'.format(parts[2])
        return ' '.join(parts)
