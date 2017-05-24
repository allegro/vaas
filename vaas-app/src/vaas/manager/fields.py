# -*- coding: utf-8 -*-

from decimal import Decimal
from django.db import models


def generate_choices(min, max, step, decimal_places=2):
    format_str = "{0:." + str(decimal_places) + "f}"
    choices = [
        (x / Decimal(step), format_str.format(x / Decimal(step))) for x in range(min, max)
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
    """
    Prevents values from being displayed with trailing 0's
    """

    def value_from_object(self, obj):
        val = super(NormalizedDecimalField, self).value_from_object(obj)
        if isinstance(val, Decimal):
            if (val.to_integral_value() == val):
                return val.to_integral_value()
            else:
                # raise Exception('MYYYYYYYYY {} {} {}'.format(val.to_integral_value(), val, val.normalize()))
                return val.normalize()


