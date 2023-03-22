# -*- coding: utf-8 -*-
from __future__ import absolute_import

from celery import Celery
from django.conf import settings

app = Celery('vaas')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.conf.update(result_extended=True)

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))


app.conf.broker_transport_options = {'max_retries': 5, 'socket_keepalive': True}
app.conf.beatx_store = settings.BROKER_URL
app.conf.beat_max_loop_interval = settings.CELERY_BEAT_MAX_LOOP_INTERVAL
app.conf.beat_schedule = {
    'refresh_backend_statuses': {
        'task': 'vaas.monitor.tasks.refresh_backend_statuses',
        'schedule': settings.BACKEND_STATUSES_UPDATE_INTERVAL_SECONDS,
    },
}
# For better handle connection errors to redis we need to setup redis_backend_health_check_interval parameter
# https://docs.celeryq.dev/en/stable/userguide/configuration.html?highlight=redis_retry_on_timeout#redis-backend-health-check-interval
app.conf.redis_backend_health_check_interval = settings.REDIS_BACKEND_HEALTH_CHECK_INTERVAL_SEC
