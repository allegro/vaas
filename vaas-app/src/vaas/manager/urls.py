# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns(
    'vaas.manager.views',
    url(r'^$', 'index'),
    url(r'^varnish/vcl/(?P<varnish_server_pk>\d+)/$', 'vcl'),
)
