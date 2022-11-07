# -*- coding: utf-8 -*-

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


def generate_choices(min, max, step, decimal_places=2):
    format_str = "{0:." + str(decimal_places) + "f}"
    choices = [
        (Decimal(format_str.format(x / Decimal(step))), format_str.format(x / Decimal(step))) for x in range(min, max)
    ]

    return choices


def make_backend_name(backend):

    ip_octets = backend.address.split('.')
    name = "_%s_%s_%s_%s_%s" % (backend.id, backend.dc.normalized_symbol, ip_octets[2], ip_octets[3], backend.port)
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
        except:  # noqa
            raise ValidationError(
                self.error_messages['invalid'],
                code='invalid',
                params={'value': value},
            )
