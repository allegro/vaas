# -*- coding: utf-8 -*-

import datetime

from django.utils.timezone import utc
from django.test import TestCase
from mock import patch, Mock
from nose.tools import assert_equals

from vaas.monitor.models import BackendStatus
from vaas.monitor.health import BackendStatusManager
from vaas.cluster.models import Dc
from vaas.manager.models import Probe, Backend, Director, TimeProfile

BACKEND_LIST_RAW_RESPONSE_V3 = """Backend name                   Refs   Admin      Probe
first_service_1_dc1_199_10_80(192.168.199.10,,80) 1      probe      Healthy 5/5
first_service_2_dc1_199_11_80(192.168.199.11,,80) 1      probe      Sick 5/5
first_service_3_dc1_199_12_80(192.168.199.12,,80) 1      probe      Healthy 5/5
deleted_backend_666_dc1_199_99_80(192.168.199.99,,80) 1      probe      Healthy 5/5
"""

BACKEND_LIST_RAW_RESPONSE_V4_1 = """Backend name                   Admin      Probe
vagrant_template_4-2016-04-20T13:01:31.254336-vol.6a200.first_service_1_dc1_199_10_80 probe      Healthy 5/5
vagrant_template_4-2016-04-20T13:01:31.254336-vol.6a200.first_service_2_dc1_199_11_80 probe      Sick 5/5
vagrant_template_4-2016-04-20T13:01:31.254336-vol.6a200.first_service_3_dc1_199_12_80 probe      Healthy 5/5
vagrant_template_4-2016-04-20T13:01:31.254336-vol.6a200.deleted_backend_666_dc1_199_99_80 probe      Healthy 5/5
"""

EXPECTED_BACKEND_TO_STATUS_MAP = {'192.168.199.10:80': 'Healthy',
                                  '192.168.199.11:80': 'Sick',
                                  '192.168.199.12:80': 'Healthy'}


class BackendStatusManagerTest(TestCase):
    def setUp(self):
        timestamp = datetime.datetime.utcnow().replace(tzinfo=utc)
        dc = Dc.objects.create(name='dc1', symbol='dc1')
        probe = Probe.objects.create(name='probe', url='/')
        director = Director.objects.create(
            name='first_service',
            mode='round_robin',
            probe_id=probe.id,
            time_profile=TimeProfile.objects.create(name='profile')
        )
        Backend.objects.create(address='192.168.199.10', port=80, director=director, dc=dc, id=1)
        Backend.objects.create(address='192.168.199.11', port=80, director=director, dc=dc, id=2)
        Backend.objects.create(address='192.168.199.12', port=80, director=director, dc=dc, id=3)
        BackendStatus.objects.create(address='192.168.199.10', port=80, status='Healthy', timestamp=timestamp)
        BackendStatus.objects.create(address='192.168.199.11', port=80, status='Sick', timestamp=timestamp)
        BackendStatus.objects.create(address='192.168.199.12', port=80, status='Healthy', timestamp=timestamp)

    def assert_status(self, expected_address, expected_port, expected_status, given_backend_status):
        assert_equals(expected_address, given_backend_status.address)
        assert_equals(expected_port, given_backend_status.port)
        assert_equals(expected_status, given_backend_status.status)

    def test_should_store_backend_statuses(self):
        backend_to_status_map = {
            '192.168.199.11:80': 'Sick',
            '192.168.199.12:80': 'Healthy'
        }
        BackendStatusManager().store_backend_statuses(backend_to_status_map)
        statuses = BackendStatus.objects.all()
        assert_equals(2, len(statuses))
        self.assert_status('192.168.199.11', 80, 'Sick', statuses[0])
        self.assert_status('192.168.199.12', 80, 'Healthy', statuses[1])

    def test_should_load_backend_statuses_from_varnish_3(self):

        varnish_api_mock = Mock()
        varnish_api_mock.fetch.return_value = (None, BACKEND_LIST_RAW_RESPONSE_V3)

        varnish_api_provider_mock = Mock()
        varnish_api_provider_mock.get_connected_varnish_api.return_value = iter([varnish_api_mock])

        with patch('vaas.monitor.health.VarnishApiProvider', return_value=varnish_api_provider_mock):
            assert_equals(EXPECTED_BACKEND_TO_STATUS_MAP, BackendStatusManager().load_from_varnish())

    def test_should_load_backend_statuses_from_varnish_4_1(self):

        varnish_api_mock = Mock()
        varnish_api_mock.fetch.return_value = (None, BACKEND_LIST_RAW_RESPONSE_V4_1)

        varnish_api_provider_mock = Mock()
        varnish_api_provider_mock.get_connected_varnish_api.return_value = iter([varnish_api_mock])

        with patch('vaas.monitor.health.VarnishApiProvider', return_value=varnish_api_provider_mock):
            assert_equals(EXPECTED_BACKEND_TO_STATUS_MAP, BackendStatusManager().load_from_varnish())

    def test_should_refresh_backend_statuses(self):
        backend_to_status_map = {
            '192.168.199.11:80': 'Sick',
            '192.168.199.12:80': 'Healthy'
        }
        with patch('vaas.monitor.health.BackendStatusManager.load_from_varnish', return_value=backend_to_status_map):
            BackendStatusManager().refresh_statuses()
            statuses = BackendStatus.objects.all()
            assert_equals(2, len(statuses))
            self.assert_status('192.168.199.11', 80, 'Sick', statuses[0])
            self.assert_status('192.168.199.12', 80, 'Healthy', statuses[1])
