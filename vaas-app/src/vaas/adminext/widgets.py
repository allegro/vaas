# -*- coding: utf-8 -*-

from django import forms


CONJUNCTION = ' && '


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
        return split_condition(value)

    def value_from_datadict(self, data, files, name):
        parts = super(ConditionWidget, self).value_from_datadict(data, files, name)
        parts[2] = '"{}"'.format(parts[2])
        return ' '.join(parts)


class ComplexConditionWidget(forms.MultiWidget):
    def __init__(self, variables, operators, *args, **kwargs):
        self.conjunction = CONJUNCTION
        self.variables = variables
        self.operators = operators
        self.base_widget = ConditionWidget(self.variables, self.operators, *args, **kwargs)
        widgets = [
            self.base_widget
        ]
        self.test = 0
        super(ComplexConditionWidget, self).__init__(widgets, *args, **kwargs)
        self.template_name = 'forms/complex_condition.html'

    def decompress(self, value):
        result = split_complex_condition(value)
        if len(result) > 1:
            self.widgets = [ConditionWidget(self.variables, self.operators) for _ in range(0, len(result))]
        return result

    def value_from_datadict(self, data, files, name):
        parts = [self.base_widget.value_from_datadict(data, files, name + '_%s' % i) for i in self.get_ids(data, name)]
        return self.conjunction.join(parts)

    def get_ids(self, data, name):
        ids = []
        prefix = '{}_'.format(name)
        for field_name in data:
            if field_name.startswith(prefix):
                field_id = int(field_name[len(prefix):].split("_")[0])
                if field_id not in ids:
                    ids.append(field_id)
        ids.sort()
        return ids


def split_complex_condition(value):
    if value:
        return value.split(CONJUNCTION)
    return ['req.url ~ ""']


def split_condition(value):
    if value:
        parts = value.split(' ')
        if len(parts) > 1:
            left = parts.pop(0)
            operator = parts.pop(0)
            right = ' '.join(parts)
            if len(right) and right[0] == '"':
                right = right[1:]
            if right[-1] == '"':
                right = right[:-1]
            return left, operator, right
    return ['req.url', '~', '']
