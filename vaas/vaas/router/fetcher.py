from concurrent import futures

from django.conf import settings
import requests


class ValidationResponse(object):

    def __init__(self, url, director, route, status_code, expected_route):
        self.url = url
        self.director = director
        self.route = route
        self.status_code = status_code
        self.expected_route = expected_route

    def __repr__(self):
        return '{}'.format(self.__dict__)

    def __eq__(self, other):
        return hasattr(other, '__dict__') and self.__dict__ == other.__dict__


class Fetcher(object):

    def check_urls(self, positive_urls):
        result = []
        with futures.ThreadPoolExecutor(max_workers=settings.FETCHER_MAX_HTTP_WORKERS) as executor:
            requests_futures = []
            for positive_url in positive_urls:
                requests_futures.append(executor.submit(self.fetch, positive_url.url, positive_url.route.pk))
        for future in futures.as_completed(requests_futures):
            result.append(future.result())
        return result

    def fetch(self, url, route_id):
        try:
            response = requests.get(url, headers={settings.VALIDATION_HEADER: '1'})
            data = {}
            try:
                data = response.json()
            finally:
                return ValidationResponse(url,
                                          data.get('director', None),
                                          data.get('route', None),
                                          response.status_code,
                                          route_id)

        except requests.exceptions.RequestException:
            return ValidationResponse(url, None, None, -1, route_id)
