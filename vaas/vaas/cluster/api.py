# -*- coding: utf-8 -*-
from tastypie.resources import ALL_WITH_RELATIONS, Resource, ModelResource
from tastypie import fields
from tastypie.authentication import ApiKeyAuthentication

from vaas.cluster.coherency import OutdatedServer, OutdatedServerManager
from vaas.cluster.forms import LogicalCLusterModelForm, DcModelForm, VclTemplateModelForm, VarnishServerModelForm, \
    VclTemplateBlockModelForm

from vaas.external.api import ExtendedDjangoAuthorization as DjangoAuthorization
from vaas.external.tasty_validation import ModelCleanedDataFormValidation
from vaas.external.serializer import PrettyJSONSerializer
from vaas.cluster.models import Dc, VarnishServer, VclTemplate, LogicalCluster, VclTemplateBlock
from vaas.external.oauth import VaasMultiAuthentication


class OutdatedServerResource(Resource):
    id = fields.IntegerField(attribute='id')
    ip = fields.CharField(attribute='ip')
    port = fields.CharField(attribute='port')
    dc = fields.CharField(attribute='dc')
    cluster = fields.CharField(attribute='cluster')
    current_vcl = fields.CharField(attribute='current_vcl', blank=True, null=True)

    class Meta:
        resource_name = 'outdated_server'
        object_class = OutdatedServer
        authorization = DjangoAuthorization()
        include_resource_uri = False
        filtering = {
            'cluster__name': ['exact'],
        }

    def get_object_list(self, request):
        cluster = None
        if request:
            cluster = request.GET.get('cluster', None)
        return OutdatedServerManager().load(cluster)

    def obj_get_list(self, bundle, **kwargs):
        return self.get_object_list(bundle.request)


class LogicalClusterResource(ModelResource):
    class Meta:
        queryset = LogicalCluster.objects.all()
        resource_name = 'logical_cluster'
        serializer = PrettyJSONSerializer()
        authorization = DjangoAuthorization()
        validation = ModelCleanedDataFormValidation(form_class=LogicalCLusterModelForm)
        authentication = VaasMultiAuthentication(ApiKeyAuthentication())
        always_return_data = True
        filtering = {
            'name': ['exact'],
            'reload_timestamp': ['exact'],
        }

    def dehydrate(self, bundle):
        bundle.data['varnish_count'] = bundle.obj.varnish_count()
        return bundle


class DcResource(ModelResource):
    class Meta:
        queryset = Dc.objects.all()
        resource_name = 'dc'
        serializer = PrettyJSONSerializer()
        authorization = DjangoAuthorization()
        authentication = VaasMultiAuthentication(ApiKeyAuthentication())
        validation = ModelCleanedDataFormValidation(form_class=DcModelForm)
        always_return_data = True
        filtering = {
            'symbol': ['exact'],
        }


class VclTemplateResource(ModelResource):

    def build_schema(self):
        base_schema = super(VclTemplateResource, self).build_schema()
        for field in self._meta.object_class._meta.fields:
            if field.name in base_schema['fields'] and field.choices:
                base_schema['fields'][field.name].update({
                    'choices': field.choices,
                })
        return base_schema

    class Meta:
        queryset = VclTemplate.objects.all()
        resource_name = 'vcl_template'
        serializer = PrettyJSONSerializer()
        authorization = DjangoAuthorization()
        authentication = VaasMultiAuthentication(ApiKeyAuthentication())
        validation = ModelCleanedDataFormValidation(form_class=VclTemplateModelForm)
        always_return_data = True
        filtering = {
            'name': ['exact'],
        }


class VarnishServerResource(ModelResource):

    cluster = fields.ForeignKey(LogicalClusterResource, 'cluster')
    template = fields.ForeignKey(VclTemplateResource, 'template')
    dc = fields.ForeignKey(DcResource, 'dc')

    class Meta:
        queryset = VarnishServer.objects.all()
        resource_name = 'varnish_server'
        serializer = PrettyJSONSerializer()
        authorization = DjangoAuthorization()
        authentication = VaasMultiAuthentication(ApiKeyAuthentication())
        validation = ModelCleanedDataFormValidation(form_class=VarnishServerModelForm)
        always_return_data = True
        filtering = {
            'ip': ['exact'],
            'port': ['exact'],
            'http_port': ['exact'],
            'cluster': ['exact']
        }


class VclTemplateBlockResource(ModelResource):

    template = fields.ForeignKey(VclTemplateResource, 'template')

    def build_schema(self):
        base_schema = super(VclTemplateBlockResource, self).build_schema()
        for field in self._meta.object_class._meta.fields:
            if field.name in base_schema['fields'] and field.choices:
                base_schema['fields'][field.name].update({
                    'choices': field.choices,
                })
        return base_schema

    class Meta:
        queryset = VclTemplateBlock.objects.all()
        resource_name = 'vcl_template_block'
        serializer = PrettyJSONSerializer()
        authorization = DjangoAuthorization()
        authentication = VaasMultiAuthentication(ApiKeyAuthentication())
        validation = ModelCleanedDataFormValidation(form_class=VclTemplateBlockModelForm)
        always_return_data = True
        filtering = {
            'name': ['exact'],
            'template': ALL_WITH_RELATIONS
        }
