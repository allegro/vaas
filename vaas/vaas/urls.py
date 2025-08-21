# -*- coding: utf-8 -*-

import django.urls as urls
from django.conf import settings
from django.urls import include, path, re_path
from django.contrib.admin.sites import NotRegistered
from django.views.generic.base import RedirectView
from django_prometheus import exports
from tastypie.api import Api

from vaas.cluster.api import ConnectCommandResource, DomainMappingResource, DcResource, VarnishServerResource, \
    VclTemplateBlockResource, ValidateVCLCommandResource, VclTemplateResource, LogicalClusterResource, \
    OutdatedServerResource
from vaas.manager.api import ProbeResource, DirectorResource, BackendResource, TimeProfileResource, \
    ReloadTaskResource
from vaas.router.api import RedirectResource, RouteResource, RouteConfigurationResource, \
    ValidateRedirectsCommandResource, ValidateRoutesCommandResource
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
v01_api.register(RedirectResource())
v01_api.register(RouteResource())
v01_api.register(RouteConfigurationResource())
v01_api.register(ConnectCommandResource())
v01_api.register(ValidateVCLCommandResource())
v01_api.register(ValidateRedirectsCommandResource())
v01_api.register(ValidateRoutesCommandResource())
v01_api.register(DomainMappingResource())

urlpatterns = [
    re_path(r'^admin/purger/', include('vaas.purger.urls')),
    re_path(r'^$', RedirectView.as_view(url='/admin/')),
    re_path(r'^manager/', include('vaas.manager.urls')),
    path('router/', include(('vaas.router.urls', 'vaas'), namespace='router')),
    re_path(r'^account/', include('vaas.account.urls')),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^api/', include(v01_api.urls)),
    path('plugins/', include(('vaas.external.urls', 'vaas'), namespace='plugins')),
    path('', include('social_django.urls', namespace='social')),
]
if settings.PROMETHEUS_ENABLE:
    urlpatterns += [
        urls.path(settings.PROMETHEUS_EXPORTER_PATH, exports.ExportToDjangoView, name="prometheus-django-metrics"),
    ]

admin.site.site_header = 'VaaS Administration'
