from datetime import timedelta
from typing import Optional, TypedDict, Union
from django.conf import settings
from prometheus_client import CollectorRegistry, Gauge, Summary, push_to_gateway

from vaas.metrics.models import Metrics


class MetricsBucket(TypedDict, total=False):
    name: str
    metric: Union[Summary, Gauge]


class PrometheusClient:
    def __init__(self) -> None:
        self.host: str = f'{settings.PROMETHEUS_GATEWAY_HOST}:{settings.PROMETHEUS_GATEWAY_PORT}'
        self.job: str = 'vaas'
        self.registry: CollectorRegistry = CollectorRegistry()

    def push(self) -> None:
        push_to_gateway(gateway=self.host, job=self.job, registry=self.registry)


class PrometheusMetrics(Metrics):
    def __init__(self) -> None:
        super().__init__(
            client=PrometheusClient())
        self.metrics_bucket: MetricsBucket = {}

    def _get_or_create(self, name: str, type: Union[Summary, Gauge]) -> Optional[Union[Summary, Gauge]]:
        name_with_suffix: str = f'{name}_microseconds'
        if name:
            metric = self.metrics_bucket.get(name_with_suffix)
            if not metric:
                self.metrics_bucket[name_with_suffix] = type(name_with_suffix, name, registry=self.client.registry) # type: ignore
                return self.metrics_bucket.get(name_with_suffix)
            return metric

    def sum(self, metric_name: str, value: timedelta) -> None:
        if metric_name:
            self._get_or_create(metric_name, Summary).observe(value.microseconds) # type: ignore

    def gauge(self, metric_name: str, value: Union[int, float]) -> None:
        if metric_name:
            self._get_or_create(metric_name, Gauge).set(value) # type: ignore