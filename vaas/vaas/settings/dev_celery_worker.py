from .dev import *

from vaas.configuration.loader import YamlConfigLoader


for key, value in YamlConfigLoader(['/configuration']).get_config_tree('config.yaml').items():
    globals()[key.upper()] = value

if 'CELERY_WORKER_BROKER_URL_BASE' in globals():
     BROKER_URL = CELERY_WORKER_BROKER_URL_BASE
     CELERY_RESULT_BACKEND = CELERY_WORKER_RESULT_BACKEND_BASE