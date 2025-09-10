# -*- coding: utf-8 -*-
import re
from typing import Optional
from django import forms
from vaas.router.models import DomainMapping
from django.core.exceptions import ValidationError
CONJUNCTION = ' && '


class PrioritySelect(forms.Select):
    def __init__(self, attrs=None, choices=()):
        super().__init__(attrs, choices)
        self.template_name = 'forms/priority.html'

    class Media:
        js = ('priority/js/priority-select.js',)


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
    def __init__(self, variables: tuple[tuple[str, str],...], operators: tuple[tuple[str, str],...], *args, **kwargs):
        widgets: tuple[forms.Select, forms.Select, forms.TextInput] = (
            forms.Select(choices=variables, attrs={'class': 'form-control', 'col': 'col-3'}),
            forms.Select(choices=operators, attrs={'class': 'form-control', 'col': 'col-3'}),
            forms.TextInput(attrs={'class': 'form-control', 'col': 'col-6'}),
        )
        super(ConditionWidget, self).__init__(widgets, *args, **kwargs)
        self.template_name = 'forms/condition.html'

    def decompress(self, value: str) -> list[str]:
        return split_condition(value)

    def value_from_datadict(self, data, files, name):
        parts = super(ConditionWidget, self).value_from_datadict(data, files, name)
        # some operators are intended to use with numbers not strings
        if parts[1] not in ('>', '<'):
            parts[2] = '"{}"'.format(parts[2])
        return ' '.join(parts)


class ComplexConditionWidget(forms.MultiWidget):
    def __init__(self, variables: tuple[tuple[str, str],...], operators: tuple[tuple[str, str],...], *args, **kwargs):
        self.conjunction = CONJUNCTION
        self.variables = variables
        self.operators = operators
        self.base_widget = ConditionWidget(self.variables, self.operators, *args, **kwargs)
        widgets = [
            self.base_widget,
        ]
        super(ComplexConditionWidget, self).__init__(widgets, *args, **kwargs)
        self.template_name = 'forms/complex_condition.html'

    def decompress(self, value: str) -> list[str]:
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


def split_complex_condition(value: str) -> list[str]:
    if value:
        return value.split(CONJUNCTION)
    return ['req.url ~ ""']


def split_condition(value: str) -> list[str]:
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
            return [left, operator, right]
    return ['req.url', '~', '']


def split_redirect_condition(value: str) -> str:
    if value:
        parts = value.split(' ')
        if len(parts) > 1:
            return parts[2][1:-1]
    return ''


class ComplexRedirectConditionWidget(forms.MultiWidget):
    def __init__(self, domains: tuple[tuple[str, str],...], attrs: Optional[dict[str, str]] = None):
        widgets = (
            forms.Select(choices=domains,
                         attrs={'class': 'form-control', 'style': 'display: inline-block; width:40%'}),
            forms.TextInput(attrs={'class': 'form-control',
                                   'style': 'display: inline-block; width:60%',
                                   'placeholder': 'Source path: ^/example([/?#].*)?$'}),
        )
        super().__init__(widgets, attrs)

    def decompress(self, value: str) -> tuple[Optional[str], str]:
        path = split_redirect_condition(value)
        domain = self.attrs.get('condition_domain', None)
        return domain, path


class ComplexRedirectConditionField(forms.MultiValueField):
    def __init__(self, **kwargs):
        domains: tuple[tuple[str, str],...] = tuple((domain.pk, domain.domain) for domain in DomainMapping.objects.all())
        fields = (
            forms.ChoiceField(choices=domains),
            forms.CharField(),
        )
        widget = ComplexRedirectConditionWidget(domains)
        super().__init__(fields=fields, widget=widget, **kwargs)

    def compress(self, data_list: list[str]) -> Optional[str]:
        if data_list:
            _, src_path = data_list
            return f"req.url ~ \"{src_path}\""
        return None


def split_rewrite_groups(value: Optional[str]) -> tuple[bool, Optional[str]]:
    if value:
        return (True, value)
    return (False, None)


class RewriteGroupsInput(forms.TextInput):
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["attrs"].update(
            {'disabled': value is None}
        )
        return context


class RewriteGroupsWidget(forms.MultiWidget):
    template_name = 'forms/rewrite_groups.html'

    def __init__(self):
        widgets = (
            forms.CheckboxInput,
            RewriteGroupsInput(attrs={'placeholder': 'Place here your regular expression for rewrite source groups'}),
        )
        super().__init__(widgets)

    def decompress(self, value):
        return split_rewrite_groups(value)


class RewriteGroupsField(forms.MultiValueField):
    widget = RewriteGroupsWidget

    def __init__(self, **kwargs):
        fields = (
            forms.BooleanField(),
            forms.CharField(),
        )
        super().__init__(fields=fields, **kwargs)

    def validate(self, value) -> None:
        super().validate(value)
        try:
            re.compile(value)
        except re.error as e:
            raise ValidationError(f"Not valid regex: {e.msg}.")

    def compress(self, data_list):
        if data_list:
            enabled, rewrite_groups = data_list
            if enabled and rewrite_groups in self.empty_values:
                raise ValidationError("This field is required")
            return rewrite_groups
        return ''
