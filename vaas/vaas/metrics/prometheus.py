import logging

from typing import Dict, Optional, Type, Union, Tuple
from django.conf import settings
from prometheus_client import Counter, CollectorRegistry, Gauge, Summary, push_to_gateway

from vaas.metrics.models import Metrics

logger = logging.getLogger(__name__)

Kind = Union[Counter, Summary, Gauge]


class PrometheusClient:
    def __init__(self) -> None:
        self.host: str = (f'{settings.PROMETHEUS_GATEWAY_HOST}:{settings.PROMETHEUS_GATEWAY_PORT}'
                          f'{settings.VICTORIAMETRICS_PATH if settings.VICTORIAMETRICS_SUPPORT else ""}')
        self.job: str = settings.PROMETHEUS_GATEWAY_JOB
        self.labels: Dict[str, str] = settings.PROMETHEUS_GATEWAY_LABELS
        self.metrics_bucket: Dict[str, Kind] = {}
        self.registry: CollectorRegistry = CollectorRegistry()

    def get_or_create(self, full_name: str, kind: Type[Kind]) -> Kind:
        metric: Optional[Kind] = self.metrics_bucket.get(full_name)
        if not metric:
            name, labels = self._split_dotted_name_to_short_name_and_labels(full_name)
            if labels:
                new_metrics: Kind = kind(name, name, labels.keys(), registry=self.registry).labels(**labels)
            else:
                new_metrics: Kind = kind(name, name, registry=self.registry)
            self.metrics_bucket[full_name] = new_metrics
        return self.metrics_bucket[full_name]

    def _split_dotted_name_to_short_name_and_labels(self, name: str) -> Tuple[str, Dict[str, str]]:
        """
        Splits dotted name for example "my_metric.label1.value1.label2.value2" into tuple containing:
        - short_name -> "my_metric"
        - labels ->  {"label1": "value1", "label2": "value2"
        """
        labels = self.labels.copy()
        parts = name.split(".")
        name = parts.pop(0)
        if len(parts) % 2 == 0:
            for i in range(0, len(parts), 2):
                labels[parts[i]] = parts[i + 1]
        return name, labels

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
