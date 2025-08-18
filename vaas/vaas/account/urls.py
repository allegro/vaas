from django.urls import path

from vaas.account.views import api_key, generate_api_key

urlpatterns = [
    path('api-key', api_key, name='api_key'),
    path('generate-api-key', generate_api_key, name='generate_api_key'),
]
