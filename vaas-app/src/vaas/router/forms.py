# -*- coding: utf-8 -*-

from django.core.exceptions import ValidationError
from django.forms import ModelForm, ModelMultipleChoiceField

from vaas.adminext.widgets import ConditionWidget, PrioritySelect, SearchableSelect
from django.contrib.admin.widgets import FilteredSelectMultiple
from vaas.cluster.models import LogicalCluster
from vaas.manager.models import Director
from vaas.router.models import Route


class RouteModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['priority'].initial = 50
        self.fields['director'].queryset = Director.objects.order_by('name')
        self.fields['clusters'] = ModelMultipleChoiceField(
            queryset=LogicalCluster.objects.order_by('name'), 
            widget=FilteredSelectMultiple(
            is_stacked=False,
            verbose_name='clusters'))
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
            'director': SearchableSelect(),
        }

    def clean_condition(self):
        condition = self.cleaned_data['condition']
        if condition.count('"') > 2:
            raise ValidationError(message='Double quotes not allowed')
        if '""' in condition:
            raise ValidationError(message='Condition cannot be empty')
        return condition
    
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
