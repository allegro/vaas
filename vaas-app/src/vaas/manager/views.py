# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponse

from vaas.manager.models import Director, Backend
from vaas.cluster.cluster import VarnishCluster


def index(request):
    director_list = Director.objects.all()
    return render_to_response('varnishgui/index.html', {'director_list': director_list})


def vcl(request, varnish_server_pk):
    return HttpResponse(VarnishCluster().get_vcl_content(int(varnish_server_pk)), content_type="text/plain")
