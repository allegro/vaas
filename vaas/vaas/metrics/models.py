from typing import Any, Protocol, Union


class Metrics:
    def __init__(self, client: Any) -> None:
        self.client = client


class MetricsProtocol(Protocol):
    def counter(self, metric_name: str) -> None:
        ...

    def sum(self, metric_name: str, value: float) -> None:
        ...

    def gauge(self, metric_name: str, value: Union[int, float]) -> None:
        ...
