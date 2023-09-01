from django.conf import settings
from typing import Union
from statsd import StatsClient

from vaas.metrics.models import Metrics


class StatsdMetrics(Metrics):
    def __init__(self) -> None:
        super().__init__(
            client=StatsClient(host=settings.STATSD_HOST, port=settings.STATSD_PORT, prefix=settings.STATSD_PREFIX)
        )

    def counter(self, metric_name: str) -> None:
        if metric_name:
            self.client.incr(metric_name)

    def sum(self, metric_name: str, value: float) -> None:
        if metric_name:
            self.client.timing(metric_name, value)

    def gauge(self, metric_name: str, value: Union[int, float]) -> None:
        if metric_name:
            self.client.gauge(metric_name, value)
