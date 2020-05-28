from json import dumps
from tastypie import fields
from tastypie.authorization import DjangoAuthorization
from tastypie.authentication import ApiKeyAuthentication
from tastypie.resources import Resource
from tastypie.http import HttpResponse, HttpApplicationError
from tastypie.exceptions import ImmediateHttpResponse, Unauthorized
from vaas.cluster.cluster import ServerExtractor
from vaas.cluster.models import LogicalCluster
from vaas.purger.purger import VarnishPurger
from vaas.external.oauth import VaasMultiAuthentication


class Purger(object):
    def __init__(self, url, clusters):
        self.url = url
        self.clusters = clusters
        self.resource_url = 1


class PurgeUrl(Resource):
    url = fields.CharField(attribute='url')
    clusters = fields.CharField(attribute='clusters')

    class Meta:
        resource_name = 'purger'
        list_allowed_methods = ['post']
        authorization = DjangoAuthorization()
        authentication = VaasMultiAuthentication(ApiKeyAuthentication())
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

        url, clusters = bundle.data['url'], bundle.data['clusters']
        purger = VarnishPurger()

        if not isinstance(clusters, list):
            clusters = [clusters]

        servers = ServerExtractor().extract_servers_by_clusters(LogicalCluster.objects.filter(name__in=clusters))
        purger_result = purger.purge_url(url, servers)
        if len(purger_result.get("error")) > 0:
             raise ImmediateHttpResponse(self.create_json_response(purger_result, HttpApplicationError))
        raise ImmediateHttpResponse(self.create_json_response(purger_result, HttpResponse))

    def get_object_list(self, request):
        return None
