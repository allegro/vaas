# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from django.views.generic.base import RedirectView
from tastypie.api import Api

from vaas.cluster.api import DcResource, VarnishServerResource, VclTemplateBlockResource, VclTemplateResource, \
    LogicalClusterResource
from vaas.manager.api import ProbeResource, DirectorResource, BackendResource, TimeProfileResource
from vaas.purger.api import PurgeUrl
from django.contrib import admin

admin.autodiscover()

v01_api = Api(api_name='v0.1')
v01_api.register(DcResource())
v01_api.register(TimeProfileResource())
v01_api.register(VarnishServerResource())
v01_api.register(ProbeResource())
v01_api.register(DirectorResource())
v01_api.register(BackendResource())
v01_api.register(VclTemplateResource())
v01_api.register(VclTemplateBlockResource())
v01_api.register(LogicalClusterResource())
v01_api.register(PurgeUrl())


urlpatterns = patterns(
    '',
    url(r'^admin/purger/', include('vaas.purger.urls')),
    url(r'^$', RedirectView.as_view(url='/admin')),
    url(r'^manager/', include('vaas.manager.urls')),
    url(r'^account/', include('vaas.account.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include(v01_api.urls)),
)
