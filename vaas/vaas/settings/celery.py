# -*- coding: utf-8 -*-
from __future__ import absolute_import

# import os
from celery import Celery
from django.conf import settings

# set the default Django settings module for the 'celery' program.
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vaas.settings.production')

app = Celery('vaas')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


app.conf.beat_schedule = {
    'refresh_backend_statuses': {
        'task': 'vaas.monitor.tasks.refresh_backend_statuses',
        'schedule': settings.BACKEND_STATUSES_UPDATE_INTERVAL_SECONDS,
    },
}
