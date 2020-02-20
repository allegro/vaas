# -*- coding: utf-8 -*-
from tastypie.resources import ModelResource, ALL_WITH_RELATIONS, Resource
from tastypie import fields
from tastypie.authentication import ApiKeyAuthentication, MultiAuthentication, SessionAuthentication
from django.conf.urls import url
from django.core.exceptions import ObjectDoesNotExist
from vaas.external.tasty_validation import ModelCleanedDataFormValidation

from vaas.external.api import ExtendedDjangoAuthorization as DjangoAuthorization
from vaas.external.serializer import PrettyJSONSerializer
from vaas.router.models import Route, provide_route_configuration
from vaas.router.forms import RouteModelForm
from vaas.adminext.widgets import split_complex_condition, split_condition
from vaas.external.oauth import VaasMultiAuthentication


class RouteResource(ModelResource):
    director = fields.ForeignKey('vaas.manager.api.DirectorResource', 'director')
    clusters = fields.ToManyField('vaas.cluster.api.LogicalClusterResource', 'clusters')

    class Meta:
        queryset = Route.objects.all().prefetch_related('clusters')
        resource_name = 'route'
        serializer = PrettyJSONSerializer()
        authorization = DjangoAuthorization()
        authentication = VaasMultiAuthentication(ApiKeyAuthentication())
        validation = ModelCleanedDataFormValidation(form_class=RouteModelForm)
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

    def dehydrate_director(self, bundle):
        return bundle.obj.director.name

    def dehydrate_clusters(self, bundle):
        return list(bundle.obj.clusters.values_list('name', flat=True))


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
