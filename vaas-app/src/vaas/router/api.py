# -*- coding: utf-8 -*-
from tastypie.resources import ModelResource, ALL_WITH_RELATIONS, Resource
from tastypie import fields
from tastypie.authentication import ApiKeyAuthentication, MultiAuthentication, SessionAuthentication
from vaas.external.tasty_validation import ModelCleanedDataFormValidation

from vaas.external.api import ExtendedDjangoAuthorization as DjangoAuthorization
from vaas.external.serializer import PrettyJSONSerializer
from vaas.router.models import Route
from vaas.router.forms import RouteModelForm
from vaas.adminext.widgets import split_condition


class RouteResource(ModelResource):
    director = fields.ForeignKey('vaas.manager.api.DirectorResource', 'director')
    clusters = fields.ToManyField('vaas.cluster.api.LogicalClusterResource', 'clusters')

    class Meta:
        queryset = Route.objects.all().prefetch_related('clusters')
        resource_name = 'route'
        serializer = PrettyJSONSerializer()
        authorization = DjangoAuthorization()
        authentication = ApiKeyAuthentication()
        validation = ModelCleanedDataFormValidation(form_class=RouteModelForm)
        always_return_data = True
        filtering = {
            'director': ALL_WITH_RELATIONS,
            'clusters': ALL_WITH_RELATIONS
        }

    def hydrate_condition(self, bundle):
        bundle.data['condition_0'], bundle.data['condition_1'], bundle.data['condition_2'] = split_condition(
            bundle.data['condition']
        )
        return bundle

    def dehydrate_director(self, bundle):
        return bundle.obj.director.name

    def dehydrate_clusters(self, bundle):
        return list(bundle.obj.clusters.values_list('name', flat=True))
