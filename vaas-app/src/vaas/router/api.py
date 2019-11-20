# -*- coding: utf-8 -*-
import logging

from django.core.exceptions import ObjectDoesNotExist

from tastypie.resources import ModelResource, ALL_WITH_RELATIONS, Resource
from tastypie import fields
from tastypie.exceptions import ApiFieldError
from tastypie.authentication import ApiKeyAuthentication, MultiAuthentication, SessionAuthentication
from vaas.external.tasty_validation import ModelCleanedDataFormValidation

from vaas.external.api import ExtendedDjangoAuthorization as DjangoAuthorization
from vaas.external.serializer import PrettyJSONSerializer
from vaas.cluster.models import LogicalCluster
from vaas.manager.models import Director
from vaas.router.models import Route
from vaas.router.forms import RouteModelForm

logger = logging.getLogger('vaas')


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

    def dehydrate_director(self, bundle):
        return bundle.obj.director.name

    def dehydrate_clusters(self, bundle):
        return list(bundle.obj.clusters.values_list('name', flat=True))

    def hydrate_director(self, bundle):
        try:
            bundle.data['director'] = Director.objects.get(name=bundle.data['director'])
        except ObjectDoesNotExist:
            logger.info("[RouteResource.hydrate_director()] provided name = %s", bundle.data['director'])
            raise ApiFieldError("Could not find the provided director via resource name '%s'."
                                % bundle.data['director'])
        return bundle

    def hydrate_clusters(self, bundle):
        try:
            bundle.data['clusters'] = LogicalCluster.objects.get(name__in=bundle.data['clusters'])
        except ObjectDoesNotExist:
            logger.info("[RouteResource.hydrate_clusters()] provided name = %s", bundle.data['clusters'])
            raise ApiFieldError("Could not find the provided cluster via resource name '%s'." % bundle.data['clusters'])
        return bundle
