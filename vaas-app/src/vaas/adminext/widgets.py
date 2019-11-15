# -*- coding: utf-8 -*-

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple


class PrioritySelect(forms.Select):
    def __init__(self, attrs=None, choices=()):
        super().__init__(attrs, choices)
        self.template_name = 'forms/priority.html'


class SearchableSelect(forms.Select):
    def __init__(self, attrs=None, choices=()):
        if attrs is None:
            attrs = {}
        attrs['class'] = 'selectpicker form-control'
        attrs['data-live-search'] = 'true'
        super().__init__(attrs, choices)

    class Media:
        css = {
            'all': ('bootstrap-select/css/bootstrap-select.min.css',)
        }
        js = ('bootstrap-select/js/bootstrap-select.min.js',)

class MultipleSelectExtended(FilteredSelectMultiple):
    def __init__(self, verbose_name, is_stacked, attrs):
        super().__init__(verbose_name, is_stacked, attrs)
    class Media:
        js = ('js/multipleselectextended.js',)
        # self.template_name = 'forms/multipleselectextended.html'

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
