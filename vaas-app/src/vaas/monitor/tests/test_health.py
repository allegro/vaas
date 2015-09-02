# -*- coding: utf-8 -*-

import datetime

from django.utils.timezone import utc
from django.test import TestCase
from mock import patch, Mock
from nose.tools import assert_equals

from vaas.monitor.models import BackendStatus
from vaas.monitor.health import BackendStatusManager


class BackendStatusManagerTest(TestCase):
    def setUp(self):
        timestamp = datetime.datetime.utcnow().replace(tzinfo=utc)
        BackendStatus.objects.create(address='127.0.0.1', port=80, status='Healthy', timestamp=timestamp)
        BackendStatus.objects.create(address='127.0.0.2', port=80, status='Sick', timestamp=timestamp)
        BackendStatus.objects.create(address='127.0.0.3', port=80, status='Healthy', timestamp=timestamp)

    def assert_status(self, expected_address, expected_port, expected_status, given_backend_status):
        assert_equals(expected_address, given_backend_status.address)
        assert_equals(expected_port, given_backend_status.port)
        assert_equals(expected_status, given_backend_status.status)

    def test_should_store_backend_statuses(self):
        backend_to_status_map = {
            '127.0.0.1:80': 'Sick',
            '127.0.0.4:80': 'Healthy'
        }
        BackendStatusManager().store_backend_statuses(backend_to_status_map)
        statuses = BackendStatus.objects.all()
        assert_equals(2, len(statuses))
        self.assert_status('127.0.0.1', 80, 'Sick', statuses[0])
        self.assert_status('127.0.0.4', 80, 'Healthy', statuses[1])

    def test_should_load_backend_statuses_from_varnish(self):

        backend_list_raw_response = 'Backend name                   Refs   Admin      Probe\n'
        backend_list_raw_response += 'default(127.0.0.1,,80)       1      probe      Sick (no probe)\n'
        backend_list_raw_response += 'default(127.0.0.4,,80)       1      probe      Healthy (no probe)\n'

        varnish_api_mock = Mock()
        varnish_api_mock.fetch.return_value = (None, backend_list_raw_response)

        varnish_api_provider_mock = Mock()
        varnish_api_provider_mock.get_varnish_api.return_value = iter([varnish_api_mock])

        expected_backend_to_status_map = {
            '127.0.0.1:80': 'Sick',
            '127.0.0.4:80': 'Healthy'
        }

        with patch('vaas.monitor.health.VarnishApiProvider', return_value=varnish_api_provider_mock):
            assert_equals(expected_backend_to_status_map, BackendStatusManager().load_from_varnish())

    def test_should_refresh_backend_statuses(self):
        backend_to_status_map = {
            '127.0.0.1:80': 'Sick',
            '127.0.0.4:80': 'Healthy'
        }
        with patch('vaas.monitor.health.BackendStatusManager.load_from_varnish', return_value=backend_to_status_map):
            BackendStatusManager().refresh_statuses()
            statuses = BackendStatus.objects.all()
            assert_equals(2, len(statuses))
            self.assert_status('127.0.0.1', 80, 'Sick', statuses[0])
            self.assert_status('127.0.0.4', 80, 'Healthy', statuses[1])
