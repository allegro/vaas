from django.conf import settings
from vaas.settings.celery import app
from vaas.monitor.health import provide_backend_status_manager


@app.task(bind=True, soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT_SECONDS)
def refresh_backend_statuses(self):
    provide_backend_status_manager().refresh_statuses()
