# -*- coding: utf-8 -*-
from http.client import BadStatusLine
from mock import patch, Mock
from django.test import TestCase
from vaas.cluster.models import VarnishServer
from vaas.purger.purger import VarnishPurger

class VarnishPurgerTest(TestCase):

    @patch('http.client.HTTPConnection.getresponse', Mock(return_value=Mock(status=200)))
    @patch('http.client.HTTPConnection.request')
    def test_should_purge_active_varnishes(self, request_mock):
        expected_message = "varnish http response code: 200, url=http://example.com/modified_resource/, headers=[('Host', 'example.com'), ('header1', 'value1')], server=127.0.0.1:80"
        servers = [VarnishServer(ip='127.0.0.1'), VarnishServer(ip='127.0.0.2')]
        response = VarnishPurger().purge_url('http://example.com/modified_resource/', servers, headers={'header1': 'value1'})
        self.assertEqual(2, len(response['success']))
        self.assertEqual(expected_message, response['success']['127.0.0.1'])
        request_mock.assert_called_with('PURGE', '/modified_resource/', body='', headers={'header1': 'value1', 'Host': 'example.com'})

    @patch('http.client.HTTPConnection.getresponse', Mock(return_value=Mock(status=200)))
    @patch('http.client.HTTPConnection.request')
    def test_should_provided_host_header_should_be_passed_tu_purged_server(self, request_mock):
        servers = [VarnishServer(ip='127.0.0.1')]
        response = VarnishPurger().purge_url('http://example.com/modified_resource/', servers, headers={'Host': 'foo.com'})
        request_mock.assert_called_with('PURGE', '/modified_resource/', body='', headers={'Host': 'foo.com'})

    @patch('http.client.HTTPConnection.request', Mock(side_effect=BadStatusLine('bad status line')))
    def test_should_report_error_on_bad_status_line(self):
        expected_error = "Bad status line from varnish server, url=http://example.com/modified_resource/, headers=[('Host', 'example.com')], server=127.0.0.3:80"
        servers = [VarnishServer(ip='127.0.0.3')]
        response = VarnishPurger().purge_url('http://example.com/modified_resource/', servers)
        self.assertEqual(1, len(response['error']))
        self.assertEqual(expected_error, response['error']['127.0.0.3'])

    @patch('http.client.HTTPConnection.request', Mock(side_effect=Exception('Unknown error')))
    def test_should_report_error_on_generic_exception(self):
        expected_error = "Unexpected error: Unknown error, url=http://example.com/modified_resource/, headers=[('Host', 'example.com')], server=127.0.0.4:80"
        servers = [VarnishServer(ip='127.0.0.4')]
        response = VarnishPurger().purge_url('http://example.com/modified_resource/', servers)
        self.assertEqual(1, len(response['error']))
        self.assertEqual(expected_error, response['error']['127.0.0.4'])
