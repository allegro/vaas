# -*- coding: utf-8 -*-
from typing import List, Optional, Tuple
from django import forms
from vaas.router.models import provide_redirect_configuration, RedirectConfiguration
from django.core.validators import RegexValidator


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


class MultiUrlWidget(forms.MultiWidget):
    def __init__(self, *args, **kwargs):
        self.base_widget = forms.URLInput(attrs={'class': 'form-control', 'col': 'col-md-8'})
        super(MultiUrlWidget, self).__init__([self.base_widget], *args, **kwargs)
        self.template_name = 'forms/multi_url.html'

    def decompress(self, value):
        if value is None:
            value = []
        if len(value) > 1:
            self.widgets = [
                forms.URLInput(attrs={'class': 'form-control', 'col': 'col-md-8'}) for _ in range(0, len(value))
            ]
            self.widgets_names = ['_%s' % i for i in range(len(self.widgets))]
        return value

    def value_from_datadict(self, data, files, name):
        return [self.base_widget.value_from_datadict(data, files, name + '_%s' % i) for i in self.get_ids(data, name)]

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


class ConditionWidget(forms.MultiWidget):
    def __init__(self, variables, operators, *args, **kwargs):
        widgets = [
            forms.Select(choices=variables, attrs={'class': 'form-control', 'col': 'col-md-2'}),
            forms.Select(choices=operators, attrs={'class': 'form-control', 'col': 'col-md-3'}),
            forms.TextInput(attrs={'class': 'form-control', 'col': 'col-md-4'}),
        ]
        super(ConditionWidget, self).__init__(widgets, *args, **kwargs)
        self.template_name = 'forms/condition.html'

    def decompress(self, value):
        return split_condition(value)

    def value_from_datadict(self, data, files, name):
        parts = super(ConditionWidget, self).value_from_datadict(data, files, name)
        # some operators are intended to use with numbers not strings
        if parts[1] not in ('>', '<'):
            parts[2] = '"{}"'.format(parts[2])
        return ' '.join(parts)

class ComplexConditionWidget(forms.MultiWidget):
    def __init__(self, variables, operators, *args, **kwargs):
        self.conjunction = CONJUNCTION
        self.variables = variables
        self.operators = operators
        self.base_widget = ConditionWidget(self.variables, self.operators, *args, **kwargs)
        widgets = [
            self.base_widget,
        ]
        self.test = 0
        super(ComplexConditionWidget, self).__init__(widgets, *args, **kwargs)
        self.template_name = 'forms/complex_condition.html'

    def decompress(self, value):
        result = split_complex_condition(value)
        if len(result) > 1:
            self.widgets = [ConditionWidget(self.variables, self.operators) for _ in range(0, len(result))]
            self.widgets_names = ['_%s' % i for i in range(len(self.widgets))]
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
class ComplexRedirectConditionWidget(forms.MultiWidget):
    def __init__(self, http_methods: Tuple, domains: Tuple, attrs=None): 
        widgets = ( 
            forms.Select(choices=http_methods, attrs={'class': 'form-control','style': 'display: inline-block; width:15%'}),
            forms.Select(choices=domains, attrs={'class': 'form-control','style': 'display: inline-block; width:40%'}),
            forms.TextInput(attrs={'class': 'form-control','style': 'display: inline-block; width:45%','placeholder': 'Source path'}),
        )
        super().__init__(widgets, attrs)

    def decompress(self, value: str) -> Tuple[str, str, str]:
        if value:
            parts = value.split(' ')
            condition_domain = self.attrs.get('condition_domain', None)
            if len(parts) > 1:
                http_method = parts[2]
                src_path = parts[6]
                return http_method[1:-1], condition_domain, src_path[1:-1]
        return 'GET','',''

class ComplexRedirectConditionField(forms.MultiValueField):
    def __init__(self, **kwargs):
        configuration: RedirectConfiguration = provide_redirect_configuration()
        http_methods: Tuple= tuple((http_method.http_method, http_method.name) for http_method in configuration.http_methods)
        domains: Tuple = tuple((domain.domain, domain.pk) for domain in configuration.domains)
        fields = (
            forms.ChoiceField(choices=http_methods),
            forms.ChoiceField(choices=domains),
            forms.CharField(validators=[RegexValidator(regex="^/.*",message="From path should be relative")]),
        )
        widget=ComplexRedirectConditionWidget(http_methods, domains)
        super().__init__(fields=fields, widget=widget, **kwargs)

    def compress(self, data_list: List) -> Optional[str]:
        if data_list:
            http_method = data_list[0]
            src_path = data_list[2]

            return f"req.method == \"{http_method}\" && req.url ~ \"{src_path}\""
        return None