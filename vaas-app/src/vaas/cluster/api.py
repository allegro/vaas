# -*- coding: utf-8 -*-

from tastypie.resources import ALL_WITH_RELATIONS
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from tastypie.authentication import ApiKeyAuthentication
from vaas.cluster.forms import LogicalCLusterModelForm, DcModelForm, VclTemplateModelForm, VarnishServerModelForm, \
    VclTemplateBlockModelForm

from vaas.external.tasty_validation import ModelCleanedDataFormValidation
from vaas.external.serializer import PrettyJSONSerializer
from vaas.cluster.models import Dc, VarnishServer, VclTemplate, LogicalCluster, VclTemplateBlock


class LogicalClusterResource(ModelResource):
    class Meta:
        queryset = LogicalCluster.objects.all()
        serializer = PrettyJSONSerializer()
        authorization = Authorization()
        validation = ModelCleanedDataFormValidation(form_class=LogicalCLusterModelForm)
        authentication = ApiKeyAuthentication()
        filtering = {
            'name': ['exact'],
        }


class DcResource(ModelResource):
    class Meta:
        queryset = Dc.objects.all()
        resource_name = 'dc'
        serializer = PrettyJSONSerializer()
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        validation = ModelCleanedDataFormValidation(form_class=DcModelForm)
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
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        validation = ModelCleanedDataFormValidation(form_class=VclTemplateModelForm)
        filtering = {
            'name': ['exact'],
        }


class VarnishServerResource(ModelResource):
    class Meta:
        queryset = VarnishServer.objects.all()
        resource_name = 'varnish_server'
        serializer = PrettyJSONSerializer()
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        validation = ModelCleanedDataFormValidation(form_class=VarnishServerModelForm)
        filtering = {
            'ip': ['exact'],
        }


class VclTemplateBlockResource(ModelResource):

    template = fields.ForeignKey(VclTemplateResource, 'template', full=True)

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
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        validation = ModelCleanedDataFormValidation(form_class=VclTemplateBlockModelForm)
        filtering = {
            'name': ['exact'],
            'template': ALL_WITH_RELATIONS
        }
