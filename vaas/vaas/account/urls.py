from django.conf.urls import url

from vaas.account.views import api_key, generate_api_key

urlpatterns = [
    url(r'^api-key$', api_key, name='api_key'),
    url(r'^generate-api-key$', generate_api_key, name='generate_api_key'),
]
