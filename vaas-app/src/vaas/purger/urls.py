# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns(
    'vaas.purger.views',
    url(r'^$', 'purge_view'),
)
