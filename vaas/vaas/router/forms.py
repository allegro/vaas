from typing import Any, List, Dict
from django.core.exceptions import ValidationError
from django.forms import ModelForm, ModelMultipleChoiceField, CheckboxInput, Select, ModelChoiceField, HiddenInput, \
    MultiValueField, BooleanField, MultiWidget, Widget, URLInput
from django.conf import settings
from vaas.adminext.widgets import ComplexConditionWidget, ComplexRedirectConditionField, \
    RewriteGroupsField, PrioritySelect, SearchableSelect, split_complex_condition
from django.contrib.admin.widgets import FilteredSelectMultiple
from vaas.cluster.models import LogicalCluster, DomainMapping
from vaas.manager.models import Director
from vaas.router.models import Route, Redirect, PositiveUrl, provide_route_configuration, RedirectAssertion


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
    clusters = ModelMultipleChoiceField(queryset=LogicalCluster.objects.order_by('name'),
                                        widget=FilteredSelectMultiple(is_stacked=False, verbose_name='clusters'))

    clusters_in_sync = BooleanField(required=False, initial=settings.CLUSTER_IN_SYNC_ENABLED,
                                    label='Clusters in sync with director',
                                    widget=HiddenInput() if settings.CLUSTER_IN_SYNC_HIDDEN else None)

    def __init__(self, *args, **kwargs):
        if kwargs.get('instance', None):
            if not kwargs.get('initial', None):
                kwargs['initial'] = {}
            # if clusters_in_sync is not manageable then forcibly set default value
            if settings.CLUSTER_IN_SYNC_HIDDEN:
                kwargs['initial']['clusters_in_sync'] = settings.CLUSTER_IN_SYNC_ENABLED

        super().__init__(*args, **kwargs)
        if self.instance.pk is None:
            self.fields['clusters_in_sync'].widget.attrs.update({'disabled': True})

        prettify_fields(self.fields.values())
        self.fields['priority'].initial = 250
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
    required_custom_header = BooleanField(required=False, label=settings.REDIRECT_CUSTOM_HEADER_LABEL)
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
        condition_domain, rewrite_groups = "", ""
        if instance := kwargs.get('instance', None):
            condition_domain = instance.src_domain.pk
            rewrite_groups = instance.rewrite_groups
        self.fields['priority'].initial = 250
        self.fields['condition'] = ComplexRedirectConditionField()
        self.fields['condition'].widget.attrs.update({'condition_domain': condition_domain})
        self.fields['destination'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Destination path'})
        if rewrite_groups:
            self.fields['preserve_query_params'].widget.attrs.update({'disabled': True})
        prettify_fields(self.fields.values())

    def clean(self) -> Dict[str, Any]:
        cleaned_data = super().clean()
        src_domain = DomainMapping.objects.get(pk=self.data['condition_0'])
        cleaned_data['src_domain'] = src_domain

        redirects = Redirect.objects.filter(
            src_domain=src_domain,
            priority=cleaned_data.get('priority'))

        if redirects.count() == 0:
            return cleaned_data
        if self.instance.pk:
            if redirects.exclude(pk=self.instance.pk).exists():
                raise ValidationError('This combination of source domain and priority already exists')
            else:
                return cleaned_data
        raise ValidationError('This combination of source domain and priority already exists')


class RedirectAssertionForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['given_url'].widget = URLInput()
        prettify_fields(self.fields.values())

    class Meta:
        model = RedirectAssertion
        fields = '__all__'


class PositiveUrlForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['url'].widget = URLInput()
        prettify_fields(self.fields.values())

    class Meta:
        model = PositiveUrl
        fields = '__all__'


def prettify_fields(fields: List[Any]) -> None:
    for field in fields:
        if isinstance(field.widget, MultiWidget):
            for widget in field.widget.widgets:
                add_form_control(widget)
        else:
            add_form_control(field.widget)


def add_form_control(widget: Widget) -> None:
    if not isinstance(widget, CheckboxInput):
        widget.attrs.update({'class': 'form-control'})
