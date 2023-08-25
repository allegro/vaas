from datetime import timedelta
from typing import Any, Union


class Metrics:
    def __init__(self, client: Any) -> None:
        self.client = client

    def sum(self, metric_name: str, value: timedelta) -> None:
        return NotImplemented()

    def gauge(self, metric_name: str, value: Union[int, float]) -> None:
        return NotImplemented()
