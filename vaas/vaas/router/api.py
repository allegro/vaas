# -*- coding: utf-8 -*-
from tastypie.resources import ModelResource, ALL_WITH_RELATIONS, Resource
from tastypie import fields
from tastypie.bundle import Bundle
from tastypie.authentication import ApiKeyAuthentication, SessionAuthentication
from tastypie.exceptions import ImmediateHttpResponse
from django.http.response import HttpResponse
from django.conf.urls import url
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import URLValidator
from vaas.external.tasty_validation import ModelCleanedDataFormValidation

from vaas.external.api import ExtendedDjangoAuthorization as DjangoAuthorization
from vaas.external.serializer import PrettyJSONSerializer
from vaas.router.models import Route, PositiveUrl, Rewrite, RewritePositiveUrl, provide_route_configuration
from vaas.router.forms import RouteModelForm
from vaas.router.report import fetch_urls_async, prepare_report_from_task
from vaas.adminext.widgets import split_complex_condition, split_condition
from vaas.external.oauth import VaasMultiAuthentication


class RewritePositiveUrlResource(Resource):
    url = fields.CharField(attribute='url')
    expected_location = fields.CharField(attribute='expected_location')

    def dehydrate(self, bundle):
        bundle = super().dehydrate(bundle)
        del bundle.data['resource_uri']
        return bundle


class RewriteResource(ModelResource):
    rewrite_positive_urls = fields.ToManyField('vaas.router.api.RewritePositiveUrlResource', 'rewrite_positive_urls', full=True)

    class Meta:
        queryset = Rewrite.objects.all().prefetch_related('rewrite_positive_urls')
        resource_name = 'rewrite'
        serializer = PrettyJSONSerializer()
        authorization = DjangoAuthorization()
        authentication = VaasMultiAuthentication(ApiKeyAuthentication())
        always_return_data = True

    def save(self, bundle, *args, **kwargs):
        rewrite_positive_urls = bundle.data.get('rewrite_positive_urls', [])
        bundle.data['rewrite_positive_urls'] = []
        bundle = super().save(bundle, *args, **kwargs)
        if len(rewrite_positive_urls) != 0:
            # if PATCH request not contains rewrite_positive_urls field we do not want to deleting existing rewrite_positive_urls
            if not self._is_patch_request_without_rewrite_positive_urls_field(rewrite_positive_urls):
                # if HTTP request contains rewrite_positive_urls we want delete previous rewrite_positive_urls attached to the Rewrite object
                bundle.obj.positive_urls.all().delete()
                for rewrite_positive_url in rewrite_positive_urls:
                    print(type(rewrite_positive_url))
                    RewritePositiveUrl.objects.create(
                        url=rewrite_positive_url['url'],
                        expected_location=rewrite_positive_url['expected_location'],
                        rewrite=bundle.obj
                    )
        else:
            bundle.obj.rewrite_positive_urls.all().delete()

        return bundle

    # If PATCH request not contains rewrite_positive_urls field, tastypie pulls out Bundle object with rewrite_positive_urls currently attached to the Rewrite object
    def _is_patch_request_without_rewrite_positive_urls_field(self, rewrite_positive_urls):
        return all(isinstance(rewrite_positive_url, Bundle) for rewrite_positive_url in rewrite_positive_urls)


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


class ValidateRoutesRequest(Resource):

    class Meta:
        resource_name = 'validate_routes'
        list_allowed_methods = ['post']
        authorization = DjangoAuthorization()
        authentication = VaasMultiAuthentication(ApiKeyAuthentication(), SessionAuthentication())
        include_resource_uri = False

    def obj_create(self, bundle, **kwargs):
        task = fetch_urls_async.delay()
        raise ImmediateHttpResponse(self.create_http_response(task.id))

    def get_object_list(self, request):
        return None

    def create_http_response(self, task_id):
        response = HttpResponse(status=202)
        response.setdefault('Location', '/api/v0.1/validation_report/{}/'.format(task_id))
        return response


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


class ValidationReportResource(Resource):
    validation_results = fields.ToManyField(ValidationResultResource, 'validation_results', full=True, null=True)
    validation_status = fields.CharField(attribute='validation_status', null=True)
    task_status = fields.CharField(attribute='task_status')

    class Meta:
        resource_name = 'validation_report'
        list_allowed_methods = ['get']
        authorization = DjangoAuthorization()
        authentication = VaasMultiAuthentication(ApiKeyAuthentication(), SessionAuthentication())
        fields = ['validation_results', 'validation_status', 'task_status']
        include_resource_uri = False

    def obj_get(self, bundle, **kwargs):
        return prepare_report_from_task(kwargs['pk'])

    def get_object_list(self, request):
        return None
