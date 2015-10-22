# -*- coding: utf-8 -*-
from httplib import BadStatusLine
from mock import patch, Mock
from django.test import TestCase
from vaas.cluster.models import VarnishServer
from vaas.purger.purger import VarnishPurger


class VarnishPurgerTest(TestCase):

    @patch('httplib.HTTPConnection.getresponse', Mock(return_value=Mock(status=200)))
    @patch('httplib.HTTPConnection.request')
    def test_should_purge_active_varnishes(self, response_mock):
        expected_message = "varnish http response code: 200, url=http://example.com/modified_resource/"
        servers = [VarnishServer(ip='127.0.0.1'), VarnishServer(ip='127.0.0.2')]
        response = VarnishPurger().purge_url('http://example.com/modified_resource/', servers)
        self.assertEqual(2, len(response['success']))
        self.assertEqual(expected_message, response['success']['127.0.0.1'])

    @patch('httplib.HTTPConnection.request', Mock(side_effect=BadStatusLine('bad status line')))
    def test_should_report_error_on_bad_status_line(self):
        expected_error = "Bad status line from varnish server, url=http://example.com/modified_resource/"
        servers = [VarnishServer(ip='127.0.0.3')]
        response = VarnishPurger().purge_url('http://example.com/modified_resource/', servers)
        self.assertEqual(1, len(response['error']))
        self.assertEqual(expected_error, response['error']['127.0.0.3'])

    @patch('httplib.HTTPConnection.request', Mock(side_effect=Exception('Unknown error')))
    def test_should_report_error_on_generic_exception(self):
        expected_error = "Unexpected error: Unknown error, url=http://example.com/modified_resource/"
        servers = [VarnishServer(ip='127.0.0.4')]
        response = VarnishPurger().purge_url('http://example.com/modified_resource/', servers)
        self.assertEqual(1, len(response['error']))
        self.assertEqual(expected_error, response['error']['127.0.0.4'])
