# -*- coding: utf-8 -*-

from django.conf.urls import url

from vaas.manager.views import vcl

urlpatterns = [
    url(r'^varnish/vcl/(?P<varnish_server_pk>\d+)/$', vcl),
]
