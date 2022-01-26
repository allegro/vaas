from django.conf import settings
from vaas.settings.celery import app
from vaas.monitor.health import BackendStatusManager

@app.task(bind=True,  soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT_SECONDS)
def refresh_backend_statuses(self):
    BackendStatusManager().refresh_statuses()