# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from django.contrib.admin.sites import NotRegistered
from django.views.generic.base import RedirectView
from tastypie.api import Api

from vaas.cluster.api import DcResource, VarnishServerResource, VclTemplateBlockResource, VclTemplateResource, \
    LogicalClusterResource, OutdatedServerResource
from vaas.manager.api import ProbeResource, DirectorResource, BackendResource, TimeProfileResource, ReloadTaskResource, RouteResource
from vaas.purger.api import PurgeUrl
from django.contrib import admin
from social_django.models import Association, Nonce, UserSocialAuth

admin.autodiscover()

try:
    admin.site.unregister(Association)
    admin.site.unregister(Nonce)
    admin.site.unregister(UserSocialAuth)
except NotRegistered:
    pass

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
v01_api.register(OutdatedServerResource())
v01_api.register(ReloadTaskResource())
v01_api.register(RouteResource())


urlpatterns = [
    url(r'^admin/purger/', include('vaas.purger.urls')),
    url(r'^$', RedirectView.as_view(url='/admin')),
    url(r'^manager/', include('vaas.manager.urls')),
    url(r'^account/', include('vaas.account.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include(v01_api.urls)),
    url(r'^plugins/', include('vaas.external.urls', namespace='plugins')),
    url('', include('social_django.urls', namespace='social')),
]

admin.site.site_header = 'VaaS Administration'
