from django.urls import re_path

from vaas.purger.views import purge_view

urlpatterns = [
    re_path("^$", purge_view, name="purge_view"),
]
