# -*- coding: utf-8 -*-
from http.client import BadStatusLine
from mock import patch, Mock, call
from django.test import TestCase
from vaas.cluster.models import VarnishServer
from vaas.purger.purger import VarnishPurger


class VarnishPurgerTest(TestCase):

    @patch('http.client.HTTPConnection.getresponse', Mock(return_value=Mock(status=200)))
    @patch('http.client.HTTPConnection.request')
    def test_should_purge_active_varnishes(self, request_mock):
        expected_message_varnish1 = [
            "varnish http response code: 200, url=http://example.com/modified_resource/, headers=[('Host', 'example.com'), ('header1', 'value1')], server=127.0.0.1:80",  # noqa
            "varnish http response code: 200, url=http://example.com/modified_resource/, headers=[('Host', 'example.com'), ('header1', 'value2')], server=127.0.0.1:80"  # noqa
        ]
        expected_message_varnish2 = [
            "varnish http response code: 200, url=http://example.com/modified_resource/, headers=[('Host', 'example.com'), ('header1', 'value1')], server=127.0.0.2:80",  # noqa
            "varnish http response code: 200, url=http://example.com/modified_resource/, headers=[('Host', 'example.com'), ('header1', 'value2')], server=127.0.0.2:80"  # noqa
        ]
        servers = [VarnishServer(ip='127.0.0.1'), VarnishServer(ip='127.0.0.2')]
        result = VarnishPurger().purge_url('http://example.com/modified_resource/', servers, headers={'header1': ['value1', 'value2']})  # noqa

        calls = [
            call('PURGE', '/modified_resource/', body='', headers={'header1': 'value1', 'Host': 'example.com'}),
            call('PURGE', '/modified_resource/', body='', headers={'header1': 'value2', 'Host': 'example.com'}),
            call('PURGE', '/modified_resource/', body='', headers={'header1': 'value1', 'Host': 'example.com'}),
            call('PURGE', '/modified_resource/', body='', headers={'header1': 'value2', 'Host': 'example.com'})
        ]
        request_mock.assert_has_calls(calls, any_order=True)

        self.assertEqual(2, len(result['success']))
        self.assertEqual(expected_message_varnish1, result['success']['127.0.0.1'])
        self.assertEqual(expected_message_varnish2, result['success']['127.0.0.2'])

    @patch('http.client.HTTPConnection.getresponse', Mock(return_value=Mock(status=200)))
    @patch('http.client.HTTPConnection.request')
    def test_should_provided_host_header_should_be_passed_tu_purged_server(self, request_mock):
        servers = [VarnishServer(ip='127.0.0.1')]
        response = VarnishPurger().purge_url('http://example.com/modified_resource/', servers, headers={'Host': ['foo.com']})  # noqa
        request_mock.assert_called_with('PURGE', '/modified_resource/', body='', headers={'Host': 'foo.com'})

    @patch('http.client.HTTPConnection.request', Mock(side_effect=BadStatusLine('bad status line')))
    def test_should_report_error_on_bad_status_line(self):
        expected_error = [
            "Bad status line from varnish server, url=http://example.com/modified_resource/, headers=[('Host', 'example.com')], server=127.0.0.3:80"  # noqa
        ]
        servers = [VarnishServer(ip='127.0.0.3')]
        response = VarnishPurger().purge_url('http://example.com/modified_resource/', servers)
        self.assertEqual(1, len(response['error']))
        self.assertEqual(expected_error, response['error']['127.0.0.3'])

    @patch('http.client.HTTPConnection.request', Mock(side_effect=Exception('Unknown error')))
    def test_should_report_error_on_generic_exception(self):
        expected_error = [
            "Unexpected error: Unknown error, url=http://example.com/modified_resource/, headers=[('Host', 'example.com')], server=127.0.0.4:80"  # noqa
        ]
        servers = [VarnishServer(ip='127.0.0.4')]
        response = VarnishPurger().purge_url('http://example.com/modified_resource/', servers)
        self.assertEqual(1, len(response['error']))
        self.assertEqual(expected_error, response['error']['127.0.0.4'])

    def test_should_prepare_headers_combinations(self):
        excepted_result = [
            {'header2': 'val1', 'header1': 'val1'},
            {'header2': 'val1', 'header1': 'val2'},
            {'header2': 'val2', 'header1': 'val1'},
            {'header2': 'val2', 'header1': 'val2'}
        ]
        headers = {
            "header1": ["val1", "val2"],
            "header2": ["val1", "val2"]
        }
        result = VarnishPurger().prepare_headers_combinations(headers)
        self.assertEqual(result, excepted_result)
