from json import dumps
from tastypie import fields
from tastypie.authorization import DjangoAuthorization
from tastypie.authentication import ApiKeyAuthentication
from tastypie.resources import Resource
from tastypie.http import HttpResponse, HttpApplicationError
from tastypie.validation import Validation
from tastypie.exceptions import ImmediateHttpResponse, Unauthorized
from vaas.cluster.cluster import ServerExtractor
from vaas.cluster.models import LogicalCluster
from vaas.purger.purger import VarnishPurger
from vaas.external.oauth import VaasMultiAuthentication
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError


validate_url = URLValidator()


class Purger(object):
    def __init__(self, url, clusters):
        self.url = url
        self.clusters = clusters
        self.resource_url = 1


class PurgeUrlValidation(Validation):
    def is_valid(self, bundle, request=None):
        if not bundle.data:
            return {'__all__': 'No data found in payload'}
        errors = {}
        if not bundle.data.get('url', None):
            errors['url'] = 'This field is required'
            return errors
        try:
            validate_url(bundle.data['url'])
        except ValidationError:
            errors['url'] = 'Provided url is not valid '
        return errors


class PurgeUrl(Resource):
    url = fields.CharField(attribute='url')
    headers = fields.DictField(attribute='headers')
    clusters = fields.CharField(attribute='clusters')

    class Meta:
        resource_name = 'purger'
        list_allowed_methods = ['post']
        authorization = DjangoAuthorization()
        authentication = VaasMultiAuthentication(ApiKeyAuthentication())
        validation = PurgeUrlValidation()
        fields = ['url', 'clusters']
        include_resource_uri = False

    def create_json_response(self, data, http_response_class):
        return http_response_class(content=dumps(data), content_type="application/json; charset=utf-8")

    def obj_create(self, bundle, **kwargs):
        try:
            if not bundle.request.user.is_staff:
                raise Unauthorized()
        except Unauthorized as e:
            self.unauthorized_result(e)
        self.is_valid(bundle)
        if bundle.errors:
            raise ImmediateHttpResponse(response=self.error_response(bundle.request, bundle.errors))
        url, clusters, headers = bundle.data['url'], bundle.data['clusters'], bundle.data.get('headers')
        purger = VarnishPurger()

        if not isinstance(clusters, list):
            clusters = [clusters]

        servers = ServerExtractor().extract_servers_by_clusters(LogicalCluster.objects.filter(name__in=clusters))
        purger_result = purger.purge_url(url, servers, headers)
        if len(purger_result.get("error")) > 0:
            raise ImmediateHttpResponse(self.create_json_response(purger_result, HttpApplicationError))
        raise ImmediateHttpResponse(self.create_json_response(purger_result, HttpResponse))

    def get_object_list(self, request):
        return None
