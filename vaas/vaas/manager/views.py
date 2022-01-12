# -*- coding: utf-8 -*-

from django.http import HttpResponse
from vaas.cluster.cluster import VarnishCluster


def vcl(request, varnish_server_pk):
    return HttpResponse(VarnishCluster().get_vcl_content(int(varnish_server_pk)), content_type="text/plain")
