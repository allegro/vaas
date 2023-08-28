from datetime import timedelta
from typing import Any, Protocol, Union


class Metrics:
    def __init__(self, client: Any) -> None:
        self.client = client


class MetricsProtocol(Protocol):
    def sum(self, metric_name: str, value: timedelta) -> None:
        ...

    def gauge(self, metric_name: str, value: Union[int, float]) -> None:
        ...