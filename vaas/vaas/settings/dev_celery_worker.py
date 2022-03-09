from .dev import *

# from vaas.configuration.loader import YamlConfigLoader


# if 'CELERY_WORKER_BROKER_URL_BASE' in globals():
#     BROKER_URL = CELERY_WORKER_BROKER_URL_BASE
#     CELERY_RESULT_BACKEND = CELERY_WORKER_RESULT_BACKEND_BASE
CELERY_BROKER_URL = 'redis://localhost:6379/1'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/2'