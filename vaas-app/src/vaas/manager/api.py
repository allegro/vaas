# -*- coding: utf-8 -*-

from tastypie.resources import ModelResource, ALL_WITH_RELATIONS
from tastypie.authorization import Authorization
from tastypie import fields
from tastypie.authentication import ApiKeyAuthentication

from vaas.external.tasty_validation import ModelCleanedDataFormValidation
from vaas.external.serializer import PrettyJSONSerializer
from vaas.cluster.api import DcResource
from vaas.manager.forms import ProbeModelForm, DirectorModelForm, BackendModelForm
from vaas.manager.models import Backend, Probe, Director
from vaas.monitor.models import BackendStatus


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
    backends = fields.ToManyField(
        'vaas.manager.api.BackendResource', 'backends', null=True,
    )

    class Meta:
        queryset = Director.objects.all()
        resource_name = 'director'
        serializer = PrettyJSONSerializer()
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        validation = ModelCleanedDataFormValidation(form_class=DirectorModelForm)
        filtering = {
            'name': ['exact'],
            'enabled': ['exact'],
            'probe': ALL_WITH_RELATIONS
        }


class BackendResource(ModelResource):
    dc = fields.ForeignKey(DcResource, 'dc', full=True)
    director = fields.ForeignKey(DirectorResource, 'director')

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
        return bundle
