from django.urls import path

from vaas.purger.views import purge_view

urlpatterns = [
    path('', purge_view, name='purge_view'),
]
