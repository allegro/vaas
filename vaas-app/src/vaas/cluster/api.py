# -*- coding: utf-8 -*-

from django.forms import ModelForm
from vaas.external.tasty_validation import ModelCleanedDataFormValidation
from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from tastypie.authentication import ApiKeyAuthentication

from vaas.external.serializer import PrettyJSONSerializer
from vaas.cluster.models import Dc, VarnishServer, VclTemplate, LogicalCluster, VclTemplateBlock


class VarnishServerModelForm(ModelForm):
    class Meta:
        model = VarnishServer


class VclTemplateBlockModelForm(ModelForm):
    class Meta:
        model = VclTemplateBlock


class DcResource(ModelResource):
    class Meta:
        queryset = Dc.objects.all()
        resource_name = 'dc'
        serializer = PrettyJSONSerializer()
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        filtering = {
            'symbol': ['exact'],
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


class VclTemplateResource(ModelResource):
    class Meta:
        queryset = VclTemplate.objects.all()
        resource_name = 'vcl_template'
        serializer = PrettyJSONSerializer()
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        filtering = {
            'name': ['exact'],
        }


class VclTemplateBlockResource(ModelResource):
    template = fields.ForeignKey(VclTemplateResource, 'template', full=True)
    class Meta:
        queryset = VclTemplateBlock.objects.all()
        resource_name = 'vcl_template_block'
        serializer = PrettyJSONSerializer()
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        validation = ModelCleanedDataFormValidation(form_class=VclTemplateBlockModelForm)
        filtering = {
            'name': ['exact'],
        }


class LogicalClusterResource(ModelResource):
    class Meta:
        queryset = LogicalCluster.objects.all()
        serializer = PrettyJSONSerializer()
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        filtering = {
            'name': ['exact'],
        }
