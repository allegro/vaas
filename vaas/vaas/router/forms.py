from typing import Any, List
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.forms import ModelForm, ModelMultipleChoiceField, CheckboxInput, Select, ModelChoiceField, HiddenInput, \
    MultiValueField, BooleanField, 	MultiWidget, Widget
from django.conf import settings
from vaas.adminext.widgets import ComplexConditionWidget, ComplexRedirectConditionField, MultiUrlWidget, RewriteGroupsField, \
    PrioritySelect, SearchableSelect, split_complex_condition
from django.contrib.admin.widgets import FilteredSelectMultiple
from vaas.cluster.models import LogicalCluster, DomainMapping
from vaas.manager.models import Director
from vaas.router.models import Route, Redirect, PositiveUrl, provide_route_configuration

class MultipleUrl(MultiValueField):
    default_error_messages = {
        'invalid': 'Enter a list of proper urls.',
        'incomplete': 'Enter a complete url.',
    }

    def clean(self, value):
        super().clean(value)
        clean_data = [v for v in value if v not in self.empty_values]
        self.widget.decompress(value)
        out = self.compress(clean_data)
        self.validate(out)
        self.run_validators(out)
        return clean_data

    def compress(self, data_list):
        return data_list

    def run_validators(self, value):
        for v in value:
            super().run_validators(v)


class RouteModelForm(ModelForm):
    positive_urls = MultipleUrl(fields='', widget=MultiUrlWidget(), validators=[URLValidator()], required=False)
    clusters = ModelMultipleChoiceField(queryset=LogicalCluster.objects.order_by('name'),
                                        widget=FilteredSelectMultiple(is_stacked=False, verbose_name='clusters'))
    clusters_in_sync = BooleanField(required=False, initial=settings.CLUSTER_IN_SYNC_ENABLED,
                                    label='Clusters in sync with director')

    def __init__(self, *args, **kwargs):
        initial_urls = []
        if kwargs.get('instance', None):
            if not kwargs.get('initial', None):
                kwargs['initial'] = {}
            initial_urls = [p.url for p in kwargs['instance'].positive_urls.all()]
            kwargs['initial']['positive_urls'] = initial_urls
        super().__init__(*args, **kwargs)
        if self.instance.pk is None:
            self.fields['clusters_in_sync'].widget.attrs.update({'disabled': True})
        pretify_fields(self.fields.values())
        self.fields['priority'].initial = 250
        self.fields['positive_urls'].widget.decompress(initial_urls)
        if hasattr(self.fields['director'], 'widget') and hasattr(self.fields['director'].widget, 'widget'):
            self.fields['director'].widget = self.fields['director'].widget.widget
            self.fields['director'].queryset = Director.objects.exclude(virtual=True).order_by('name')

    class Meta:
        model = Route
        fields = '__all__'
        configuration = provide_route_configuration()
        widgets = {
            'condition': ComplexConditionWidget(
                variables=tuple((left.left, left.name) for left in configuration.lefts),
                operators=tuple((operator.operator, operator.name) for operator in configuration.operators)
            ),
            'action': Select(
                choices=tuple((action.action, action.name) for action in configuration.actions)
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
        existing_urls = instance.positive_urls.values_list('url', flat=True)
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
        if self.cleaned_data.get('clusters_in_sync'):
            if not self.cleaned_data.get('clusters'):
                self.cleaned_data['clusters'] = []
                del self._errors['clusters']
            if 'clusters' in self.changed_data:
                if self.instance.pk is not None:
                    self.cleaned_data['clusters'] = self.instance.clusters.all()
        cleaned_data = super(RouteModelForm, self).clean()
        if self._errors:
            return cleaned_data

        if cleaned_data.get('clusters_in_sync'):
            clusters = cleaned_data.get('director').cluster.values_list('id', flat=True)
        else:
            clusters = cleaned_data.get('clusters')
        routes_with_sync = Route.objects.filter(
            clusters_in_sync=True,
            director=cleaned_data.get('director'),
            priority=cleaned_data.get('priority'),
            director__cluster__in=clusters)

        routes_without_sync = Route.objects.filter(
            clusters_in_sync=False,
            director=cleaned_data.get('director'),
            priority=cleaned_data.get('priority'),
            clusters__id__in=clusters)

        routes = routes_with_sync | routes_without_sync

        routes_count = routes.count()
        if routes_count == 0:
            return
        if self.instance.pk:
            if routes.exclude(pk=self.instance.pk).exists():
                raise ValidationError('This combination of director, cluster and priority already exists')
            else:
                return
        raise ValidationError('This combination of director, cluster and priority already exists')
class RedirectModelForm(ModelForm):
    preserve_query_params = BooleanField(required=False, label='Preserve query params')
    src_domain = ModelChoiceField(queryset=DomainMapping.objects.all(), widget=HiddenInput(), required=False)
    rewrite_groups = RewriteGroupsField(required=False)
    class Meta:
        model = Redirect
        fields = '__all__'
        widgets = {
            'priority': PrioritySelect(
                choices=tuple([(i, i) for i in range(1, 500)]),
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        condition_domain = ""
        if instance := kwargs.get('instance', None):
            condition_domain = instance.src_domain.pk
        self.fields['priority'].initial = 250
        self.fields['condition'] = ComplexRedirectConditionField()
        self.fields['condition'].widget.attrs.update({'condition_domain': condition_domain})
        self.fields['destination'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Destination path'})
        pretify_fields(self.fields.values())

    def clean(self) -> None:
        cleaned_data = super().clean()
        src_domain = DomainMapping.objects.get(pk=self.data['condition_1'])
        cleaned_data['src_domain'] = src_domain
        return cleaned_data

def pretify_fields(fields: List[Any]) -> None:
    for field in fields:
        if isinstance(field.widget, MultiWidget):
            for widget in field.widget.widgets:
                add_form_control(widget)
        else:
            add_form_control(field.widget)

def add_form_control(widget: Widget) -> None:
    if not isinstance(widget, CheckboxInput):
        widget.attrs.update({'class': 'form-control'})