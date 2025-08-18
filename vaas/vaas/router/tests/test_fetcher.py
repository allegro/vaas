import requests
import requests_mock
from django.test import TestCase

from vaas.router.models import Route, PositiveUrl, Redirect, RedirectAssertion
from vaas.router.fetcher import Fetcher, RouteAssertionResponse, RedirectAssertionResponse


class TestFetcher(TestCase):

    def test_should_fetch_validation_data_for_url(self):
        with requests_mock.Mocker() as m:
            m.register_uri('GET',
                           'http://test.com/first-route',
                           json={'director': 'first', 'route': 1},
                           status_code=203)
            expected_response = {'status_code': 203, 'director': 'first', 'route': 1}
            self.assertEqual(
                expected_response, Fetcher()._fetch('http://test.com/first-route', Fetcher.ROUTE_VALIDATION)
            )

    def test_should_return_validation_data_on_connection_exception(self):
        with requests_mock.Mocker() as m:
            m.register_uri('GET', 'http://test.com/first-route', exc=requests.exceptions.ConnectTimeout)
            expected_response = {'status_code': 0}
            self.assertEqual(
                expected_response, Fetcher()._fetch('http://test.com/first-route', Fetcher.ROUTE_VALIDATION)
            )

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
            expected_responses = [RouteAssertionResponse('http://test.com/first-route', 'first', 1, 203, 1),
                                  RouteAssertionResponse('http://test.com/second-route', 'first', 1, 203, 1)
                                  ]
            self.assertCountEqual(expected_responses, fetcher.check_urls(positive_urls))

    def test_should_check_redirect_assertions(self):
        redirect = Redirect(pk=1)
        redirect_assertions = [
            RedirectAssertion(given_url='http://redirect.me.com/one', expected_location='/new-one', redirect=redirect),
            RedirectAssertion(given_url='http://redirect.me.com/two', expected_location='/new-two', redirect=redirect),
        ]

        with requests_mock.Mocker() as m:
            m.register_uri('GET',
                           'http://redirect.me.com/one',
                           json={'location': '/new-one', 'redirect': 1},
                           status_code=203)
            m.register_uri('GET',
                           'http://redirect.me.com/two',
                           json={'location': '/new-two', 'redirect': 1},
                           status_code=203)
            expected_responses = [
                RedirectAssertionResponse('http://redirect.me.com/one', '/new-one', 1, '/new-one', 1, 203),
                RedirectAssertionResponse('http://redirect.me.com/two', '/new-two', 1, '/new-two', 1, 203),
            ]
            self.assertCountEqual(expected_responses, Fetcher().check_redirects(redirect_assertions))
