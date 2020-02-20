# -*- coding: utf-8 -*-

from django.core.exceptions import ValidationError
from django.forms import ModelForm, ModelMultipleChoiceField, Select

from vaas.adminext.widgets import ComplexConditionWidget, PrioritySelect, SearchableSelect, split_complex_condition
from django.contrib.admin.widgets import FilteredSelectMultiple
from vaas.cluster.models import LogicalCluster
from vaas.manager.models import Director
from vaas.router.models import Route, provide_route_configuration


class RouteModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['priority'].initial = 250
        self.fields['director'].queryset = Director.objects.order_by('name')
        self.fields['clusters'] = ModelMultipleChoiceField(
            queryset=LogicalCluster.objects.order_by('name'),
            widget=FilteredSelectMultiple(is_stacked=False, verbose_name='clusters')
        )
        for related in ('clusters', 'director'):
            if hasattr(self.fields[related].widget, 'widget'):
                self.fields[related].widget = self.fields[related].widget.widget

    class Meta:
        model = Route
        fields = '__all__'
        configuration = provide_route_configuration()
        widgets = {
            'condition': ComplexConditionWidget(
                variables=tuple((l.left, l.name) for l in configuration.lefts),
                operators=tuple((o.operator, o.name) for o in configuration.operators)
            ),
            'action': Select(
                choices=tuple((a.action, a.name) for a in configuration.actions)
            ),
            'priority': PrioritySelect(
                choices=tuple([(i, i) for i in range(1, 500)]),
            ),
            'director': SearchableSelect(),
        }

    def clean_condition(self):
        complex_condition = self.cleaned_data['condition']

        for condition in split_complex_condition(complex_condition):
            if condition.count('"') > 2:
                raise ValidationError(message='Double quotes not allowed')
            if '""' in condition:
                raise ValidationError(message='Condition cannot be empty')
        return self.cleaned_data['condition']

    def clean(self):
        cleaner_data = super(RouteModelForm, self).clean()
        if self._errors:
            return cleaner_data
        routes = Route.objects.filter(
            director=cleaner_data.get('director'),
            priority=cleaner_data.get('priority'),
            clusters__id__in=cleaner_data.get('clusters'))
        routes_count = routes.count()
        if routes_count == 0:
            return
        if self.instance.pk:
            if routes.exclude(pk=self.instance.pk).exists():
                raise ValidationError('This combination of director, cluster and priority already exists')
            else:
                return
        raise ValidationError('This combination of director, cluster and priority already exists')
