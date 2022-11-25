from concurrent import futures
from typing import List, Callable, Any

from django.conf import settings
import requests

from vaas.router.models import RedirectAssertion, PositiveUrl


class RouteAssertionResponse:

    def __init__(self, url: str, director: str, route: int, status_code: int, expected_route: int):
        self.url = url
        self.director = director
        self.route = route
        self.status_code = status_code
        self.expected_route = expected_route

    def __repr__(self) -> str:
        return '{}'.format(self.__dict__)

    def __eq__(self, other: Any) -> bool:
        return hasattr(other, '__dict__') and self.__dict__ == other.__dict__


class RedirectAssertionResponse:
    def __init__(
            self, url: str, actual_location: str, actual_redirect: int, expected_location: str, expected_redirect: int,
            status_code: int
    ):
        self.url = url
        self.actual_location = actual_location
        self.actual_redirect = actual_redirect
        self.expected_location = expected_location
        self.expected_redirect = expected_redirect
        self.status_code = status_code

    def __repr__(self) -> str:
        return '{}'.format(self.__dict__)

    def __eq__(self, other: Any) -> bool:
        return hasattr(other, '__dict__') and self.__dict__ == other.__dict__


class Fetcher:
    def check_urls(self, assertions: List[PositiveUrl]) -> List[RouteAssertionResponse]:
        return self._check_assertions([(a.url, a.route.pk) for a in assertions], self._assert_route)

    def check_redirects(self, assertions: List[RedirectAssertion]) -> List[RedirectAssertionResponse]:
        return self._check_assertions(
            [(a.given_url, a.expected_location, a.redirect.pk) for a in assertions], self._assert_redirect)

    def _assert_route(self, url: str, route_id: int) -> RouteAssertionResponse:
        data = self._fetch(url)
        return RouteAssertionResponse(
            url, data.get('director', ''), data.get('route', 0), data.get('status_code', 0), route_id
        )

    def _assert_redirect(self, url: str, location: str, redirect_id: int) -> RedirectAssertionResponse:
        data = self._fetch(url)
        return RedirectAssertionResponse(
            url, data.get('location', ''), data.get('redirect', 0), location, redirect_id, data.get('status_code', 0)
        )

    def _check_assertions(self, assertions: list, callback: Callable) -> list:
        result = []
        with futures.ThreadPoolExecutor(max_workers=settings.FETCHER_MAX_HTTP_WORKERS) as executor:
            requests_futures = []
            for args in assertions:
                requests_futures.append(executor.submit(callback, *args))
        for future in futures.as_completed(requests_futures):
            result.append(future.result())
        return result

    def _fetch(self, url):
        data = {'status_code': 0}
        try:
            response = requests.get(url, headers={settings.VALIDATION_HEADER: '1'})
            data = {'status_code': response.status_code}
            data.update(response.json())
        finally:
            return data
