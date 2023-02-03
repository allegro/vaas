# -*- coding: utf-8 -*-
from typing import Any, List

from celery.result import AsyncResult
from django.urls import re_path
from tastypie.resources import ModelResource, ALL_WITH_RELATIONS, Resource
from tastypie import fields
from tastypie.bundle import Bundle
from tastypie.authentication import ApiKeyAuthentication, SessionAuthentication
from tastypie.exceptions import NotFound, ApiFieldError
from django.conf.urls import url
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import URLValidator
from vaas.external.tasty_validation import ModelCleanedDataFormValidation

from vaas.external.api import ExtendedDjangoAuthorization as DjangoAuthorization
from vaas.external.serializer import PrettyJSONSerializer
from vaas.router.models import Route, PositiveUrl, Redirect, RedirectAssertion, provide_route_configuration
from vaas.router.forms import RouteModelForm
from vaas.router.report import fetch_urls_async, fetch_redirects_async, prepare_report_from_task, to_dict
from vaas.adminext.widgets import split_complex_condition, split_condition, split_rewrite_groups, \
    split_redirect_condition
from vaas.external.oauth import VaasMultiAuthentication
from vaas.cluster.models import DomainMapping
from vaas.router.forms import RedirectModelForm


class RedirectAssertionResource(Resource):
    given_url = fields.CharField(attribute='given_url')
    expected_location = fields.CharField(attribute='expected_location')

    def dehydrate(self, bundle):
        bundle = super().dehydrate(bundle)
        del bundle.data['resource_uri']
        return bundle


class RedirectResource(ModelResource):
    src_domain = fields.ForeignKey('vaas.cluster.api.DomainMappingResource', 'src_domain')
    assertions = fields.ToManyField(
        'vaas.router.api.RedirectAssertionResource', 'assertions', full=True, null=True)

    class Meta:
        queryset = Redirect.objects.all().prefetch_related('assertions', 'src_domain')
        resource_name = 'redirect'
        serializer = PrettyJSONSerializer()
        authorization = DjangoAuthorization()
        authentication = VaasMultiAuthentication(ApiKeyAuthentication())
        validation = ModelCleanedDataFormValidation(form_class=RedirectModelForm)
        always_return_data = True

    def dehydrate_src_domain(self, bundle):
        return bundle.obj.src_domain.domain

    def hydrate_rewrite_groups(self, bundle):
        rewrite_groups = bundle.data.get('rewrite_groups', None)
        bundle.data['rewrite_groups_0'], bundle.data['rewrite_groups_1'] = split_rewrite_groups(rewrite_groups)
        return bundle

    def hydrate_src_domain(self, bundle):
        if src_domain := bundle.data.get('src_domain', None):
            try:
                domain = DomainMapping.objects.get(domain=src_domain)
                bundle.data['src_domain'] = domain
            except ObjectDoesNotExist:
                raise ApiFieldError(f"Domain mapping not found for domain: {src_domain}")
        return bundle

    def hydrate_condition(self, bundle):
        condition = bundle.data.get('condition', None)
        bundle.data['condition_0'] = bundle.data['src_domain'].pk
        bundle.data['condition_1'] = split_redirect_condition(condition)
        return bundle

    def save(self, bundle, *args, **kwargs):
        assertions = bundle.data.get('assertions', [])
        bundle.data['assertions'] = []
        bundle = super().save(bundle, *args, **kwargs)
        # if PATCH request not contains assertions field
        # we do not want to delete existing assertions
        if not self._is_patch_request_without_assertions_field(assertions):
            self._update_assertions(bundle.obj, assertions)
        return bundle

    def _update_assertions(self, redirect: Redirect, new_assertions: List[dict]) -> None:
        to_add = []
        to_delete = redirect.get_hashed_assertions_pks()
        for assertion in new_assertions:
            h = hash((assertion['given_url'], assertion['expected_location']))
            if h in to_delete:
                to_delete.pop(h)
            else:
                assertion['redirect'] = redirect
                to_add.append(RedirectAssertion(**assertion))
        if len(to_add):
            redirect.assertions.bulk_create(to_add)
        if len(to_delete):
            redirect.assertions.filter(pk__in=to_delete.values()).delete()

    # If PATCH request not contains redirect_assertions field,
    # tastypie pulls out Bundle object with rewrite_positive_urls currently attached to the Redirect object
    def _is_patch_request_without_assertions_field(self, redirect_assertions):
        return all(isinstance(assertion, Bundle) for assertion in redirect_assertions)


class RouteModelCleanedDataFormValidation(ModelCleanedDataFormValidation):
    def is_valid(self, bundle, request=None):
        positive_urls = bundle.data['positive_urls']
        validate_url = URLValidator()
        errors = super().is_valid(bundle, request)
        try:
            for positive_url in positive_urls:
                validate_url(positive_url)
        except Exception:
            errors['positive_urls'] = 'Enter a list of proper urls'
        return errors


class PositiveUrlResource(Resource):
    url = fields.CharField(attribute='url')

    def dehydrate(self, bundle):
        bundle = super().dehydrate(bundle)
        del bundle.data['resource_uri']
        return bundle


class RouteResource(ModelResource):
    director = fields.ForeignKey('vaas.manager.api.DirectorResource', 'director')
    clusters = fields.ToManyField('vaas.cluster.api.LogicalClusterResource', 'clusters')
    positive_urls = fields.ToManyField('vaas.router.api.PositiveUrlResource', 'positive_urls', full=True)

    class Meta:
        queryset = Route.objects.all().prefetch_related('clusters', 'positive_urls')
        resource_name = 'route'
        serializer = PrettyJSONSerializer()
        authorization = DjangoAuthorization()
        authentication = VaasMultiAuthentication(ApiKeyAuthentication())
        validation = RouteModelCleanedDataFormValidation(form_class=RouteModelForm)
        always_return_data = True
        filtering = {
            'director': ALL_WITH_RELATIONS,
            'clusters': ALL_WITH_RELATIONS,
            'condition': ['icontains']
        }

    def hydrate_condition(self, bundle):
        for i, condition in enumerate(split_complex_condition(bundle.data['condition'])):
            for j, part in enumerate(split_condition(condition)):
                bundle.data['condition_{}_{}'.format(i, j)] = part
        return bundle

    def full_hydrate(self, bundle):
        positive_urls = bundle.data.get('positive_urls', [])
        bundle = super().full_hydrate(bundle)
        bundle.data['positive_urls'] = [p['url'] for p in positive_urls]
        return bundle

    def dehydrate_director(self, bundle):
        return bundle.obj.director.name

    def dehydrate_clusters(self, bundle):
        if bundle.obj.clusters_in_sync:
            return []
        return list(bundle.obj.clusters.values_list('name', flat=True))

    def save(self, bundle, *args, **kwargs):
        positive_urls = bundle.data.get('positive_urls', [])
        bundle = super().save(bundle, *args, **kwargs)
        bundle.obj.positive_urls.exclude(url__in=positive_urls).delete()
        existing_urls = bundle.obj.positive_urls.values_list('url', flat=True)
        for positive_url in positive_urls:
            if positive_url not in existing_urls:
                PositiveUrl.objects.create(url=positive_url, route=bundle.obj)
        return bundle


class LeftResource(Resource):
    left = fields.CharField(attribute='left')
    name = fields.CharField(attribute='name')

    class Meta:
        include_resource_uri = False


class ActionResource(Resource):
    action = fields.CharField(attribute='action')
    name = fields.CharField(attribute='name')

    class Meta:
        include_resource_uri = False


class OperatorResource(Resource):
    operator = fields.CharField(attribute='operator')
    name = fields.CharField(attribute='name')

    class Meta:
        include_resource_uri = False


class RouteConfigurationResource(Resource):
    lefts = fields.ToManyField(LeftResource, 'lefts', full=True)
    actions = fields.ToManyField(ActionResource, 'actions', full=True)
    operators = fields.ToManyField(OperatorResource, 'operators', full=True)

    class Meta:
        resource_name = 'route_config'
        list_allowed_methods = ['get']
        authorization = DjangoAuthorization()
        authentication = VaasMultiAuthentication(ApiKeyAuthentication())
        fields = ['lefts', 'actions', 'operators']
        include_resource_uri = False

    def prepend_urls(self):
        return [
            url(
                r"^(?P<resource_name>%s)/$" % self._meta.resource_name,
                self.wrap_view('dispatch_detail'),
                name="api_dispatch_detail"
            ),
        ]

    def obj_get(self, bundle, **kwargs):
        if 'pk' in kwargs:
            raise ObjectDoesNotExist()
        return provide_route_configuration()

    def get_object_list(self, request):
        return None


class NamedResource(Resource):
    id = fields.IntegerField(attribute='id', null=True)
    name = fields.CharField(attribute='name', null=True)

    class Meta:
        include_resource_uri = False


class AssertionResource(Resource):
    route = fields.ToOneField(NamedResource, attribute='route', full=True, null=True)
    director = fields.ToOneField(NamedResource, attribute='director', full=True, null=True)

    class Meta:
        include_resource_uri = False


class ValidationResultResource(Resource):
    url = fields.CharField(attribute='url')
    result = fields.CharField(attribute='result')
    expected = fields.ToOneField(AssertionResource, attribute='expected', full=True, null=True)
    current = fields.ToOneField(AssertionResource, attribute='current', full=True, null=True)
    error_message = fields.CharField(attribute='error_message', null=True)

    class Meta:
        include_resource_uri = False


class ValidateCommandModel:
    def __init__(
            self,
            pk: str = "",
            status: Any = "PENDING",
            output: Any = None):
        self.pk = pk
        self.id = pk
        self.status = status
        self.output = output

    def __repr__(self) -> str:
        return '{}'.format({k: v for k, v in self.__dict__})


class AbstractValidateCommandResource(Resource):
    pk = fields.CharField(attribute='id', readonly=True)
    status = fields.CharField(attribute='status', readonly=True, blank=True, null=True)
    output = fields.DictField(attribute='output', readonly=True, blank=True, null=True)

    class Meta:
        list_allowed_methods = []
        detail_allowed_methods = ['put', 'get']
        authorization = DjangoAuthorization()
        authentication = VaasMultiAuthentication(ApiKeyAuthentication(), SessionAuthentication())
        fields = ['status', 'output']
        include_resource_uri = False
        always_return_data = True
        name = ''

    def obj_update(self, bundle, **kwargs):
        bundle.data['pk'] = kwargs['pk']
        raise NotFound()

    def prepend_urls(self):
        return [
            re_path(r"^{}/validate-command/(?P<pk>[\w\d_.-]+)/$".format(self.Meta.name),
                    self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
            re_path(r"^{}/validate-command/$".format(self.Meta.name),
                    self.wrap_view('dispatch_list'), name="api_dispatch_list")]

    def obj_get(self, bundle, **kwargs):
        task = AsyncResult(kwargs['pk'])
        return ValidateCommandModel(
            kwargs['pk'], task.status, output=to_dict(prepare_report_from_task(kwargs['pk'], self.Meta.name))
        )

    def obj_create(self, bundle, **kwargs):
        self.order_command(kwargs['pk'])
        bundle.obj = self.obj_get(bundle, pk=kwargs['pk'])
        return bundle

    def order_command(self, pk):
        raise NotImplementedError()


class ValidateRedirectsCommandResource(AbstractValidateCommandResource):
    class Meta(AbstractValidateCommandResource.Meta):
        # prefixing the name with underscores forces prepend_urls to be matched
        # before urls linked to other resources
        name = 'redirect'
        resource_name = '__validate-redirect-command'

    def order_command(self, pk):
        return fetch_redirects_async.apply_async(task_id=pk)


class ValidateRoutesCommandResource(AbstractValidateCommandResource):
    class Meta(AbstractValidateCommandResource.Meta):
        # prefixing the name with underscores forces prepend_urls to be matched
        # before urls linked to other resources
        name = 'route'
        resource_name = '__validate-route-command'

    def order_command(self, pk):
        return fetch_urls_async.apply_async(task_id=pk)
