# -*- coding: utf-8 -*-

from django.urls import re_path

from vaas.manager.views import vcl

urlpatterns = [
    re_path(r'^varnish/vcl/(?P<varnish_server_pk>\d+)/$', vcl),
]
