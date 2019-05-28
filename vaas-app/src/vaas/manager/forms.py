# -*- coding: utf-8 -*-
import re

from django.core.exceptions import ValidationError
from django.forms import ModelForm, CheckboxSelectMultiple, FileField, Select
from vaas.manager.models import Probe, Director, Backend, TimeProfile, Route
from vaas.manager.fields import ConditionWidget
from vaas.cluster.helpers import BaseHelpers


class ProbeModelForm(ModelForm):
    class Meta:
        model = Probe
        fields = '__all__'


class TimeProfileModelForm(ModelForm):
    class Meta:
        model = TimeProfile
        fields = '__all__'


class DirectorModelForm(ModelForm):
    class Meta:
        widgets = {
            'cluster': CheckboxSelectMultiple()
        }
        model = Director
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(DirectorModelForm, self).__init__(*args, **kwargs)
        self.fields['probe'].queryset = Probe.objects.order_by('name')

    def clean_name(self):
        data = self.cleaned_data['name']
        regex_result = re.findall(BaseHelpers.dynamic_regex_with_datacenters(), data)
        if len(regex_result) > 0:
            raise ValidationError(message='Director name cannot be used with a preceeding number')
        return data


class BackendModelForm(ModelForm):
    class Meta:
        model = Backend
        fields = '__all__'

    def _clean_fields(self):
        for name, field in self.fields.items():
            if field.disabled:
                value = self.get_initial_for_field(field, name)
            else:
                value = field.widget.value_from_datadict(self.data, self.files, self.add_prefix(name))

            try:
                if isinstance(field, FileField):
                    initial = self.get_initial_for_field(field, name)
                    value = field.clean(value, initial)
                else:
                    # workaroud for decimal fields
                    if hasattr(field, '_coerce'):
                        value = field.coerce(value)
                    value = field.clean(value)
                self.cleaned_data[name] = value
                if hasattr(self, 'clean_%s' % name):
                    value = getattr(self, 'clean_%s' % name)()
                    self.cleaned_data[name] = value
            except ValidationError as e:
                self.add_error(name, e)


class RouteModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = Route
        fields = '__all__'
        widgets = {
            'condition': ConditionWidget(
                variables=(('req.url', 'URL'), ('req.http.Host', 'Domain'),),
                operators=(('==', 'exact'), ('!=', 'is different'), ('~', 'match'))
            ),
            'priority': Select(
                choices=([(i, i)for i in range(1, 100)]),
            )
        }

    def clean_condition(self):
        condition = self.cleaned_data['condition']
        if condition.count('"') > 2:
            raise ValidationError(message='Double quotes not allowed')
        return condition
