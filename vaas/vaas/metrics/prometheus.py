import logging

from typing import Dict, Optional, Type, Union
from django.conf import settings
from prometheus_client import Counter, CollectorRegistry, Gauge, Summary, push_to_gateway

from vaas.metrics.models import Metrics

logger = logging.getLogger(__name__)

Kind = Union[Counter, Summary, Gauge]


class PrometheusClient:
    def __init__(self) -> None:
        self.host: str = f'{settings.PROMETHEUS_GATEWAY_HOST}:{settings.PROMETHEUS_GATEWAY_PORT}'
        self.job: str = settings.PROMETHEUS_GATEWAY_JOB
        self.metrics_bucket: Dict[str, Kind] = {}
        self.registry: CollectorRegistry = CollectorRegistry()

    def get_or_create(self, name: str, kind: Type[Kind]) -> Kind:
        metric: Optional[Kind] = self.metrics_bucket.get(name)
        if not metric:
            new_metrics: Kind = kind(name, name, registry=self.registry)
            self.metrics_bucket[name] = new_metrics
            return new_metrics
        return metric

    def push(self) -> None:
        try:
            push_to_gateway(gateway=self.host, job=self.job, registry=self.registry)
        except Exception:
            logger.exception('PrometheusClient: cannot push metric to vmagent')


class PrometheusMetrics(Metrics):
    def __init__(self) -> None:
        super().__init__(
            client=PrometheusClient())
        
    def counter(self, metric_name: str) -> None:
        if metric_name:
            self.client.get_or_create(metric_name, Counter).inc()
            self.client.push()

    def sum(self, metric_name: str, value: float) -> None:
        if metric_name:
            self.client.get_or_create(metric_name, Summary).observe(value)
            self.client.push()

    def gauge(self, metric_name: str, value: Union[int, float]) -> None:
        if metric_name:
            self.client.get_or_create(metric_name, Gauge).set(value)
            self.client.push()
