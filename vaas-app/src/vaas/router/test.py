from django.conf import settings
from vaas.settings.celery import app
import time


@app.task(bind=True, soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT_SECONDS)
def make_routes_test(self):
    return 'OK'
