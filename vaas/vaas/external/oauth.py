import importlib
from django.conf import settings
from tastypie.authentication import Authentication, MultiAuthentication

# If Oauth for API is enabled & custom module (OAUTH_AUTH_MODULE) is not present,
# default TastyPie OAuthAuthentication backend will be used

API_ALLOW_ALL = getattr(settings, 'API_ALLOW_ALL', False)
API_OAUTH_ENABLED = getattr(settings, 'API_OAUTH_ENABLED', False)
OAUTH_AUTH_MODULE = getattr(settings, 'OAUTH_AUTH_MODULE', 'tastypie.authentication')

if API_OAUTH_ENABLED:
    oauth_module = importlib.import_module(OAUTH_AUTH_MODULE)
    OAuthAuthentication = getattr(oauth_module, 'OAuthAuthentication')


class VaasMultiAuthentication(MultiAuthentication):
    def __init__(self, *backends, **kwargs):
        super(MultiAuthentication, self).__init__(**kwargs)
        if API_OAUTH_ENABLED:
            backends = backends + (OAuthAuthentication(),)
        # AllowAll is added last to the list, as it is possible
        # that the user may have been authenticated by previous backends
        if API_ALLOW_ALL:
            backends = backends + (Authentication(),)
        self.backends = backends
