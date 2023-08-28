import logging

from datetime import timedelta
from typing import Dict, Optional, Protocol, Union
from django.conf import settings
from prometheus_client import CollectorRegistry, Gauge, Summary, push_to_gateway
from prometheus_client.metrics import MetricWrapperBase

from vaas.metrics.models import Metrics

logger = logging.getLogger(__name__)

class CollectorProtocol(Protocol):
    def __call__(self, name: str, documentation: str, registry: CollectorRegistry) -> MetricWrapperBase:
        ...

class PrometheusClient:
    def __init__(self) -> None:
        self.host: str = f'{settings.PROMETHEUS_GATEWAY_HOST}:{settings.PROMETHEUS_GATEWAY_PORT}'
        self.job: str = settings.PROMETHEUS_GATEWAY_JOB
        self.metrics_bucket: Dict[str, CollectorProtocol] = {}
        self.registry: CollectorRegistry = CollectorRegistry()

    def get_or_create(self, name: str, type: CollectorProtocol) -> CollectorProtocol:
        name_with_suffix: str = f'{name}_microseconds'
        metric: Optional[CollectorProtocol] = self.metrics_bucket.get(name_with_suffix)
        if not metric:
            self.metrics_bucket[name_with_suffix] = type(name_with_suffix, name, registry=self.registry) # type: ignore
            return self.metrics_bucket.get(name_with_suffix) # type: ignore
        return metric

    def push(self) -> None:
        try:
            push_to_gateway(gateway=self.host, job=self.job, registry=self.registry)
        except Exception as e:
            logger.exception(f'PrometheusClient: cannot push metric to vmagent')
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