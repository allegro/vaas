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

app.conf.beatx_store = settings.BROKER_URL
app.conf.beat_max_loop_interval = settings.CELERY_BEAT_MAX_LOOP_INTERVAL
app.conf.beat_schedule = {
    'refresh_backend_statuses': {
        'task': 'vaas.monitor.tasks.refresh_backend_statuses',
        'schedule': settings.BACKEND_STATUSES_UPDATE_INTERVAL_SECONDS,
    },
}

# After redis conenction troubles 'Connection closed by server / Connection by peer' we allow to re-queued
# task which was executed when failure occurred. "We know what we are doing."
# https://docs.celeryq.dev/en/latest/userguide/configuration.html#task-reject-on-worker-lost
app.conf.task_reject_on_worker_lost = settings.CELERY_TASK_REJECT_ON_WORKER_LOST
app.conf.broker_transport_options = {
    'health_check_interval': 10,
}
# For better handle redis ConenctionError exception we give possibility to configure keepalive and connect_timeout parameters
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#redis-socket-keepalive
app.conf.redis_socket_keepalive = settings.CELERY_REDIS_SOCKET_KEEPALIVE
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#redis-retry-on-timeout
app.conf.redis_retry_on_timeout = settings.CELERY_REDIS_RETRY_ON_TIMEOUT
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#redis-socket-connect-timeout
app.conf.redis_socket_connect_timeout = settings.CELERY_REDIS_SOCKET_CONNECT_TIMEOUT
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#redis-socket-timeout
app.conf.redis_socket_timeout = settings.CELERY_REDIS_SOCKET_TIMEOUT
# https://docs.celeryq.dev/en/stable/userguide/configuration.html?highlight=redis_retry_on_timeout#redis-backend-health-check-interval
app.conf.redis_backend_health_check_interval = settings.CELERY_REDIS_BACKEND_HEALTH_CHECK_INTERVAL
