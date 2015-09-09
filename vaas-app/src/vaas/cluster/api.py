# -*- coding: utf-8 -*-

from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from tastypie.authentication import ApiKeyAuthentication

from vaas.external.serializer import PrettyJSONSerializer
from vaas.cluster.models import Dc, VarnishServer, VclTemplate


class DcResource(ModelResource):
    class Meta:
        queryset = Dc.objects.all()
        resource_name = 'dc'
        allowed_methods = ['get', 'put', 'post']
        excludes = ['id']
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
        allowed_methods = ['get']
        excludes = ['id']
        serializer = PrettyJSONSerializer()
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        filtering = {
            'ip': ['exact'],
        }


class VclTemplateResource(ModelResource):
    class Meta:
        queryset = VclTemplate.objects.all()
        resource_name = 'vcl_template'
        allowed_methods = ['get']
        excludes = ['id']
        serializer = PrettyJSONSerializer()
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        filtering = {
            'name': ['exact'],
        }
