from datetime import timedelta
from django.conf import settings
from vaas.metrics.prometheus import PrometheusMetrics
from vaas.metrics.statsd import StatsdMetrics


class MetricsHandler:
    def __init__(self) -> None:
        self.prometheus = PrometheusMetrics()
        self.statsd = StatsdMetrics()

    def time(self, metric_name: str, value: timedelta) -> None:
        if settings.STATSD_ENABLE:
            self.statsd.sum(metric_name, value)

        if settings.PROMETHEUS_ENABLE:
            self.prometheus.sum(metric_name, value)
            self.prometheus.client.push()

    def gauge(self, metric_name: str, value: int):
        if settings.STATSD_ENABLE:
            self.statsd.gauge(metric_name, value)

        if settings.PROMETHEUS_ENABLE:
            self.prometheus.gauge(metric_name, value)
            self.prometheus.client.push()

metrics = MetricsHandler()