import logging
import os
from django.conf.urls import url, include


logger = logging.getLogger(__name__)


urlpatterns = []

PLUGIN_DIR = os.path.abspath(os.path.dirname(__file__))

for app in next(os.walk(PLUGIN_DIR))[1]:
    try:
        urlpatterns.append(url(r'{}/'.format(app), include('{}.urls'.format(app))))
        logger.info('Found urls for plugin: {}'.format(app))
    except ImportError as e:
        pass

