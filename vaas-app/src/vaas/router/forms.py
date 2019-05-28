# -*- coding: utf-8 -*-
import re

from django.core.exceptions import ValidationError
from django.forms import ModelForm, Select
from vaas.router.models import Route
from vaas.router.fields import ConditionWidget


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
