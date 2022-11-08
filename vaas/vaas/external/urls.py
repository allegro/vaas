import logging
import os
from django.conf.urls import url, include
from django.conf import settings


logger = logging.getLogger(__name__)


urlpatterns = []

PLUGIN_DIR = os.path.abspath('{}/../../../plugins/'.format(os.path.dirname(__file__)))


def iterate_plugins():
    for app in getattr(settings, 'INSTALLED_PLUGINS', []):
        yield app
    try:
        for app in next(os.walk(PLUGIN_DIR))[1]:
            yield app
    except StopIteration:
        return


for app in iterate_plugins():
    try:
        urlpatterns.append(url(r'{}/'.format(app), include('{}.urls'.format(app))))
        logger.info('Found urls for plugin: {}'.format(app))
    except ImportError:
        pass
