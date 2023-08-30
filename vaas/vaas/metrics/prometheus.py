import logging

from typing import Dict, Union
from django.conf import settings
from prometheus_client import CollectorRegistry, Gauge, Summary, push_to_gateway

from vaas.metrics.models import Metrics

logger = logging.getLogger(__name__)


class PrometheusClient:
    def __init__(self) -> None:
        self.host: str = f'{settings.PROMETHEUS_GATEWAY_HOST}:{settings.PROMETHEUS_GATEWAY_PORT}'
        self.job: str = settings.PROMETHEUS_GATEWAY_JOB
        self.metrics_bucket: Dict[str, Union[Summary, Gauge]] = {}
        self.registry: CollectorRegistry = CollectorRegistry()

    def get_or_create(self, name: str, type: Union[Summary, Gauge]) -> Union[Summary, Gauge, None]:
        metric: Union[Summary, Gauge, None] = self.metrics_bucket.get(name)
        if not metric:
            self.metrics_bucket[name] = type(name, name, registry=self.registry)  # type: ignore
            return self.metrics_bucket.get(name)
        return metric

    def push(self) -> None:
        try:
            push_to_gateway(gateway=self.host, job=self.job, registry=self.registry)
        except Exception:
            logger.exception('PrometheusClient: cannot push metric to vmagent')
            pass


class PrometheusMetrics(Metrics):
    def __init__(self) -> None:
        super().__init__(
            client=PrometheusClient())

    def sum(self, metric_name: str, value: float) -> None:
        if metric_name:
            self.client.get_or_create(metric_name, Summary).observe(value)
            self.client.push()

    def gauge(self, metric_name: str, value: Union[int, float]) -> None:
        if metric_name:
            self.client.get_or_create(metric_name, Gauge).set(value)
            self.client.push()
