# -*- coding: utf-8 -*-

from django.conf.urls import url

from vaas.purger.views import purge_view

urlpatterns = [
    url(r'^$', purge_view, name='purge_view'),
]
