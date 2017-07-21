# -*- coding: utf-8 -*-
import logging

from tastypie.resources import ModelResource, ALL_WITH_RELATIONS
from tastypie.authorization import Authorization
from tastypie import fields
from tastypie.fields import ListField
from tastypie.authentication import ApiKeyAuthentication, MultiAuthentication, SessionAuthentication

from vaas.external.tasty_validation import ModelCleanedDataFormValidation
from vaas.external.serializer import PrettyJSONSerializer
from vaas.cluster.api import DcResource
from vaas.manager.forms import ProbeModelForm, DirectorModelForm, BackendModelForm, TimeProfileModelForm
from vaas.manager.models import Backend, Probe, Director, TimeProfile
from vaas.monitor.models import BackendStatus


class TimeProfileResource(ModelResource):
    class Meta:
        queryset = TimeProfile.objects.all()
        resource_name = 'time_profile'
        serializer = PrettyJSONSerializer()
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        validation = ModelCleanedDataFormValidation(form_class=TimeProfileModelForm)
        filtering = {
            'max_connections': ['exact'],
            'connect_timeout': ['exact'],
            'first_byte_timeout': ['exact'],
            'between_bytes_timeout': ['exact']
        }


class ProbeResource(ModelResource):
    class Meta:
        queryset = Probe.objects.all()
        resource_name = 'probe'
        serializer = PrettyJSONSerializer()
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        validation = ModelCleanedDataFormValidation(form_class=ProbeModelForm)
        filtering = {
            'name': ['exact'],
            'url': ['exact'],
            'expected_response': ['exact']
        }


class DirectorResource(ModelResource):
    probe = fields.ForeignKey(ProbeResource, 'probe', full=True)
    time_profile = fields.ForeignKey(TimeProfileResource, 'time_profile', full=True)
    backends = fields.ToManyField(
        'vaas.manager.api.BackendResource', 'backends', null=True
    )
    cluster = fields.ToManyField(
        'vaas.cluster.api.LogicalClusterResource', 'cluster', null=False
    )

    class Meta:
        queryset = Director.objects.all()
        resource_name = 'director'
        serializer = PrettyJSONSerializer()
        authorization = Authorization()
        authentication = MultiAuthentication(ApiKeyAuthentication(), SessionAuthentication())
        validation = ModelCleanedDataFormValidation(form_class=DirectorModelForm)
        filtering = {
            'name': ['exact'],
            'enabled': ['exact'],
            'probe': ALL_WITH_RELATIONS,
            'cluster': ALL_WITH_RELATIONS
        }

    def save_m2m(self, bundle):
        logger = logging.getLogger('vaas')
        try:
            new_uris = bundle.obj.new_clusters_uris
            bundle.obj.new_clusters = [cluster.obj for cluster in bundle.data['cluster']
                            if cluster.data['resource_uri'] in new_uris]
            logger.info("[DirectorResource.save_m2m()] new_clusters = {}".format(bundle.obj.new_clusters))
        except (AttributeError, KeyError):
            pass

        return super(DirectorResource, self).save_m2m(bundle)

    def update_in_place(self, request, original_bundle, new_data):
        logger = logging.getLogger('vaas')
        try:
            original_bundle.obj.old_clusters = list(original_bundle.obj.cluster.all())
        except AttributeError:
            original_bundle.obj.old_clusters = []
        logger.info("[DirectorResource.update_in_place()] old_clusters = {}".format(original_bundle.obj.old_clusters))
        try:
            original_bundle.obj.new_clusters_uris = new_data['cluster']
        except KeyError:
            original_bundle.obj.new_clusters_uris = []
        original_bundle.obj.new_data = new_data

        return super(DirectorResource, self).update_in_place(request, original_bundle, new_data)


class BackendResource(ModelResource):
    dc = fields.ForeignKey(DcResource, 'dc', full=True)
    director = fields.ForeignKey(DirectorResource, 'director')
    tags = ListField()

    class Meta:
        queryset = Backend.objects.all()
        resource_name = 'backend'
        serializer = PrettyJSONSerializer()
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        validation = ModelCleanedDataFormValidation(form_class=BackendModelForm)
        filtering = {
            'dc': ALL_WITH_RELATIONS,
            'director': ALL_WITH_RELATIONS,
            'address': ['exact'],
            'port': ['exact']
        }

    def dehydrate(self, bundle):
        status = BackendStatus.objects.filter(address=bundle.data['address'],
                                              port=bundle.data['port'])
        if len(status) > 0:
            bundle.data['status'] = status[0].status
        else:
            bundle.data['status'] = "Unknown"

        bundle.data['time_profile'] = {
            'max_connections': bundle.obj.director.time_profile.max_connections,
            'connect_timeout': bundle.obj.director.time_profile.connect_timeout,
            'first_byte_timeout': bundle.obj.director.time_profile.first_byte_timeout,
            'between_bytes_timeout': bundle.obj.director.time_profile.between_bytes_timeout
        }

        return bundle

    def build_filters(self, filters=None, ignore_bad_filters=False):
        if filters is None:
            filters = {}

        orm_filters = super(BackendResource, self).build_filters(filters, ignore_bad_filters=ignore_bad_filters)

        if 'tag' in filters:
            orm_filters['tags__name__in'] = filters['tag'].split(',')
        return orm_filters

    def dehydrate_tags(self, bundle):
        return map(str, bundle.obj.tags.all())

    def hydrate_tags(self, bundle):
        if isinstance(bundle.data.get('tags'), list):
            bundle.data['tags'] = ','.join(bundle.data['tags'])
        elif bundle.data.get('tags') is None:
            bundle.data['tags'] = ''
        return bundle

    def save_m2m(self, bundle):
        tags = bundle.data.get('tags', [])
        bundle.obj.tags.set(*tags)
        return super(BackendResource, self).save_m2m(bundle)
