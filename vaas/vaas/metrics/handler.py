from django.conf import settings
from typing import List
from vaas.metrics.prometheus import PrometheusMetrics
from vaas.metrics.statsd import StatsdMetrics
from vaas.metrics.models import MetricsProtocol


class MetricsHandler:
    def __init__(self, protocols: List[MetricsProtocol]):
        self.protocols: List[MetricsProtocol] = protocols

    def time(self, metric_name: str, value: float) -> None:
        for protocol in self.protocols:
            protocol.sum(metric_name, value)

    def gauge(self, metric_name: str, value: int):
        for protocol in self.protocols:
            protocol.gauge(metric_name, value)


protocols: List[MetricsProtocol] = []
if settings.PROMETHEUS_ENABLE:
    protocols.append(PrometheusMetrics())

if settings.STATSD_ENABLE:
    protocols.append(StatsdMetrics())


metrics = MetricsHandler(protocols)
