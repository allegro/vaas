import requests
import requests_mock
from unittest import TestCase

from vaas.router.models import Route, PositiveUrl
from vaas.router.fetcher import Fetcher, ValidationResponse


class TestFetcher(TestCase):

    def test_should_fetch_validation_data_for_url(self):
        with requests_mock.Mocker() as m:
            m.register_uri('GET',
                           'http://test.com/first-route',
                           json={'director': 'first', 'route': 1},
                           status_code=203)
            fetcher = Fetcher()
            expected_response = ValidationResponse('http://test.com/first-route', 'first', 1, 203, 1)
            self.assertEqual(expected_response, fetcher.fetch('http://test.com/first-route', 1))

    def test_should_return_validation_data_on_connection_exception(self):
        with requests_mock.Mocker() as m:
            m.register_uri('GET', 'http://test.com/first-route', exc=requests.exceptions.ConnectTimeout)
            fetcher = Fetcher()
            expected_response = ValidationResponse('http://test.com/first-route', None, None, -1, 1)
            self.assertEqual(expected_response, fetcher.fetch('http://test.com/first-route', 1))

    def test_should_check_positive_urls(self):
        route = Route(pk=1)
        positive_urls = [
            PositiveUrl(url='http://test.com/first-route', route=route,),
            PositiveUrl(url='http://test.com/second-route', route=route,)
        ]

        with requests_mock.Mocker() as m:
            m.register_uri('GET',
                           'http://test.com/first-route',
                           json={'director': 'first', 'route': 1},
                           status_code=203)
            m.register_uri('GET',
                           'http://test.com/second-route',
                           json={'director': 'first', 'route': 1},
                           status_code=203)
            fetcher = Fetcher()
            expected_responses = [ValidationResponse('http://test.com/first-route', 'first', 1, 203, 1),
                                  ValidationResponse('http://test.com/second-route', 'first', 1, 203, 1)
                                  ]
            self.assertCountEqual(expected_responses, fetcher.check_urls(positive_urls))
