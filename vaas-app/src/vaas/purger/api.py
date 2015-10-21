from tastypie.authorization import Authorization
from tastypie.authentication import ApiKeyAuthentication
from tastypie.resources import Resource
from tastypie.http import HttpResponse
from tastypie.exceptions import ImmediateHttpResponse
from json import dumps
from vaas.purger.purger import VarnishPurger
from tastypie import fields


class PurgeUrl(Resource):
    url = fields.CharField(attribute='url')
    clusters = fields.CharField(attribute='clusters')

    class Meta:
        resource_name = 'purger'
        list_allowed_methods = ['post']
        authorization = Authorization()
        authentication = ApiKeyAuthentication()
        fields = ['url', 'clusters']
        include_resource_uri = False

    def create_json_response(self, data, http_response_class):
        return http_response_class(content=dumps(data), content_type="application/json; charset=utf-8")

    def obj_create(self, bundle, **kwargs):
        url, clusters = bundle.data['url'], bundle.data['clusters']
        purger = VarnishPurger()
        raise ImmediateHttpResponse(self.create_json_response(purger.purge_url(url, clusters), HttpResponse))

    def get_object_list(self, request):
        return None
