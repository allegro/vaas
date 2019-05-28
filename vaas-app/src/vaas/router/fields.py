# -*- coding: utf-8 -*-

from decimal import Decimal

from django import forms


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
