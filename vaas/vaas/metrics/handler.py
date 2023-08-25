from datetime import timedelta
from typing import Optional
from django.conf import settings
from vaas.metrics.prometheus import PrometheusMetrics
from vaas.metrics.statsd import StatsdMetrics


class MetricsHandler:
    def __init__(self, prometheus_metrics: Optional[PrometheusMetrics] = None,
                 statsd_metrics: Optional[StatsdMetrics] = None) -> None:
        self.prometheus: Optional[PrometheusMetrics] = prometheus_metrics
        self.statsd: Optional[StatsdMetrics] = statsd_metrics

    def time(self, metric_name: str, value: timedelta) -> None:
        if self.statsd:
            self.statsd.sum(metric_name, value)

        if self.prometheus:
            self.prometheus.sum(metric_name, value)

    def gauge(self, metric_name: str, value: int):
        if self.statsd:
            self.statsd.gauge(metric_name, value)

        if self.prometheus:
            self.prometheus.gauge(metric_name, value)

metrics = MetricsHandler(
    prometheus_metrics=PrometheusMetrics() if settings.PROMETHEUS_ENABLE else None,
    statsd_metrics=StatsdMetrics() if settings.STATSD_ENABLE else None
)