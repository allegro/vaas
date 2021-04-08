# -*- coding: utf-8 -*-

from django.conf.urls import url

from vaas.router.views import priorities

urlpatterns = [
    url(r'^route/priorities/(?P<director_id>\d+)/(?P<route_id>\d+)/(?P<current>\d+)/$', priorities, name='priorities'),
]
