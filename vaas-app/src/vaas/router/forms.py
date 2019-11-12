# -*- coding: utf-8 -*-

from django.core.exceptions import ValidationError
from django.forms import ModelForm

from vaas.adminext.widgets import ConditionWidget, PrioritySelect, SearchableSelect
from vaas.cluster.models import LogicalCluster
from vaas.manager.models import Director
from vaas.router.models import Route


class RouteModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['priority'].initial = 50
        self.fields['clusters'].queryset = LogicalCluster.objects.order_by('name')
        self.fields['director'].queryset = Director.objects.order_by('name')
        for related in ('clusters', 'director'):
            if hasattr(self.fields[related].widget, 'widget'):
                self.fields[related].widget = self.fields[related].widget.widget

    class Meta:
        model = Route
        fields = '__all__'
        widgets = {
            'condition': ConditionWidget(
                variables=(('req.url', 'URL'), ('req.http.Host', 'Domain'),),
                operators=(('==', 'exact'), ('!=', 'is different'), ('~', 'match'))
            ),
            'priority': PrioritySelect(
                choices=([(i, i)for i in range(1, 100)]),
            ),
            'clusters': SearchableSelect(),
            'director': SearchableSelect(),
        }

    def clean_condition(self):
        condition = self.cleaned_data['condition']
        if condition.count('"') > 2:
            raise ValidationError(message='Double quotes not allowed')
        if '""' in condition:
            raise ValidationError(message='Condition cannot be empty')
        return condition
