from django.conf.urls import patterns, url

urlpatterns = patterns(
    'vaas.account.views',
    url(r'^api-key$', 'api_key', name='api_key'),
    url(r'^generate-api-key$', 'generate_api_key', name='generate_api_key'),
)
