# -*- coding: utf-8 -*-
import logging

from django.core.exceptions import ObjectDoesNotExist

from tastypie.resources import ModelResource, ALL_WITH_RELATIONS, Resource
from tastypie import fields
from tastypie.exceptions import ApiFieldError
from tastypie.authentication import ApiKeyAuthentication, MultiAuthentication, SessionAuthentication

from vaas.external.api import ExtendedDjangoAuthorization as DjangoAuthorization
from vaas.external.serializer import PrettyJSONSerializer
from vaas.cluster.models import LogicalCluster
from vaas.manager.models import Director
from vaas.router.models import Route


logger = logging.getLogger('vaas')


class RouteResource(ModelResource):
    director = fields.ForeignKey('vaas.manager.api.DirectorResource', 'director')
    cluster = fields.ForeignKey('vaas.cluster.api.LogicalClusterResource', 'cluster')

    class Meta:
        queryset = Route.objects.all()
        resource_name = 'route'
        serializer = PrettyJSONSerializer()
        authorization = DjangoAuthorization()
        authentication = ApiKeyAuthentication()
        always_return_data = True
        filtering = {
            'director': ALL_WITH_RELATIONS,
            'cluster': ALL_WITH_RELATIONS
        }

    def dehydrate_director(self, bundle):
        return bundle.obj.director.name

    def dehydrate_cluster(self, bundle):
        return bundle.obj.cluster.name

    def hydrate_director(self, bundle):
        try:
            bundle.data['director'] = Director.objects.get(name=bundle.data['director'])
        except ObjectDoesNotExist:
            logger.info("[RouteResource.hydrate_director()] provided name = %s", bundle.data['director'])
            raise ApiFieldError("Could not find the provided director via resource name '%s'."
                                % bundle.data['director'])
        return bundle

    def hydrate_cluster(self, bundle):
        try:
            bundle.data['cluster'] = LogicalCluster.objects.get(name=bundle.data['cluster'])
        except ObjectDoesNotExist:
            logger.info("[RouteResource.hydrate_cluster()] provided name = %s", bundle.data['cluster'])
            raise ApiFieldError("Could not find the provided cluster via resource name '%s'." % bundle.data['cluster'])
        return bundle
