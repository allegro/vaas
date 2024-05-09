from django.conf import settings
from vaas.settings.celery import app
from vaas.monitor.health import provide_backend_status_manager


@app.task(bind=True, acks_late=settings.CELERY_TASK_ACKS_LATE,
          reject_on_worker_lost=settings.CELERY_TASK_REJECT_ON_WORKER_LOST,
          soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT_SECONDS)
def refresh_backend_statuses(self):
    provide_backend_status_manager().refresh_statuses()
