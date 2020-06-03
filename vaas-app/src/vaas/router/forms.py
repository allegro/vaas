# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.forms import ModelForm, ModelMultipleChoiceField, Select, MultiValueField

from vaas.adminext.widgets import ComplexConditionWidget, MultiUrlWidget, PrioritySelect, SearchableSelect, \
    split_complex_condition
from django.contrib.admin.widgets import FilteredSelectMultiple
from vaas.cluster.models import LogicalCluster
from vaas.manager.models import Director
from vaas.router.models import Route, PositiveUrl, provide_route_configuration


class MultipleUrl(MultiValueField):
    def clean(self, value):
        return value


class RouteModelForm(ModelForm):
    positive_urls = MultipleUrl(widget=MultiUrlWidget())

    def __init__(self, *args, **kwargs):
        initial_urls = []
        if kwargs.get('instance', None):
            if not kwargs.get('initial', None):
                kwargs['initial'] = {}
            initial_urls = [p.url for p in kwargs['instance'].positive_urls.all()]
            kwargs['initial']['positive_urls'] = initial_urls
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['priority'].initial = 250
        self.fields['director'].queryset = Director.objects.order_by('name')
        self.fields['clusters'] = ModelMultipleChoiceField(
            queryset=LogicalCluster.objects.order_by('name'),
            widget=FilteredSelectMultiple(is_stacked=False, verbose_name='clusters')
        )
        self.fields['positive_urls'].widget.decompress(initial_urls)
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

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)
        instance.save()
        instance.positive_urls.exclude(url__in=self.cleaned_data['positive_urls']).delete()
        existing_urls = [p.url for p in instance.positive_urls.all()]
        for url in self.cleaned_data['positive_urls']:
            if url not in existing_urls:
                PositiveUrl.objects.create(url=url, route=instance)
        return instance

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
