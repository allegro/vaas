# -*- coding: utf-8 -*-
from celery.result import AsyncResult
from django.db.models import Count
from django.urls.conf import re_path

from tastypie.resources import ALL_WITH_RELATIONS, Resource, ModelResource
from tastypie import fields
from tastypie.authentication import ApiKeyAuthentication
from tastypie.exceptions import NotFound, ImmediateHttpResponse
from tastypie.validation import Validation

from vaas.cluster.cluster import connect_command
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
        queryset = LogicalCluster.objects.annotate(Count('varnishserver')).all()
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
        if hasattr(bundle.obj, 'varnishserver__count'):
            bundle.data['varnish_count'] = bundle.obj.varnishserver__count
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
        queryset = VarnishServer.objects.select_related('dc').prefetch_related('template', 'cluster').all()
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


class CommandResource:
    def __init__(self, pk=None, varnish_ids=None, status=None, output=None):
        self.pk = pk
        self.id = pk
        self.varnish_ids = varnish_ids
        self.status = status
        self.output = output

    def __repr__(self):
        return '{}'.format(self.__dict__)


class CommandInputValidation(Validation):
    def is_valid(self, bundle, request=None):
        errors = {}
        try:
            varnishes = [int(varnish_id) for varnish_id in set(bundle.data.get('varnish_ids', []))]
            assert VarnishServer.objects.filter(pk__in=varnishes).count() == len(varnishes)
        except:  # noqa
            errors['varnish_ids'] = 'Provided varnish identifiers are not valid'
        else:
            task = AsyncResult(bundle.data['pk'])
            if task.args and set(task.args[0]) != set(varnishes):
                errors['__all__'] = 'Command: %s has been already ordered with another varnish_ids set' \
                                    % bundle.data['pk']

        return errors


class ConnectCommandResource(Resource):
    pk = fields.CharField(attribute='id', readonly=True)
    varnish_ids = fields.ListField(attribute='varnish_ids')
    status = fields.CharField(attribute='status', readonly=True, blank=True, null=True)
    output = fields.DictField(attribute='output', readonly=True, blank=True, null=True)

    class Meta:
        resource_name = 'connect-command'
        list_allowed_methods = []
        detail_allowed_methods = ['put', 'get']
        authorization = DjangoAuthorization()
        authentication = VaasMultiAuthentication(ApiKeyAuthentication())
        validation = CommandInputValidation()
        fields = ['input', 'status', 'output']
        include_resource_uri = False
        always_return_data = True

    def obj_update(self, bundle, **kwargs):
        bundle.data['pk'] = kwargs['pk']
        self.run_validation(bundle)
        raise NotFound()

    def obj_create(self, bundle, **kwargs):
        bundle.obj = CommandResource(pk=kwargs['pk'])
        bundle = self.full_hydrate(bundle)
        task = connect_command.apply_async([bundle.obj.varnish_ids], task_id=bundle.obj.pk)
        bundle.obj.status = task.status
        bundle.obj.output = task.result
        return bundle

    def hydrate_varnish_ids(self, bundle):
        bundle.obj.varnish_ids = bundle.data['varnish_ids']
        return bundle

    def obj_get(self, bundle, **kwargs):
        task = AsyncResult(kwargs['pk'])
        varnish_ids = []
        if task.args and len(task.args):
            varnish_ids = task.args[0]
        return CommandResource(kwargs['pk'], varnish_ids, task.status, output=task.result)

    def get_object_list(self, request):
        return []

    def run_validation(self, bundle):
        self.is_valid(bundle)
        if bundle.errors:
            raise ImmediateHttpResponse(response=self.error_response(bundle.request, bundle.errors))

    def prepend_urls(self):
        return [
            re_path(r"^varnish_server/(?P<resource_name>%s)/(?P<pk>[\w\d_.-]+)/$" % self._meta.resource_name,
                    self.wrap_view('dispatch_detail'), name="api_dispatch_detail"),
        ]
