# -*- coding: utf-8 -*-

import datetime

from django.utils.timezone import utc
from django.test import TestCase
from unittest.mock import patch, Mock
from nose.tools import assert_equals


from vaas.monitor.models import BackendStatus
from vaas.monitor.health import BackendStatusManager
from vaas.cluster.models import Dc
from vaas.manager.models import Probe, Backend, Director, TimeProfile


BACKEND_LIST_RAW_RESPONSE_V4_1 = """Backend name                   Admin      Probe
vagrant_template_4-20160420_13_01_31-vol_6a200.first_service_1_dc1_199_10_80 probe      Healthy 5/5
vagrant_template_4-20160420_13_01_31-vol_6a200.first_service_2_dc1_199_11_80 probe      Sick 5/5
vagrant_template_4-20160420_13_01_31-vol_6a200.first_service_3_dc1_199_12_80 probe      Healthy 5/5
vagrant_template_4-20160420_13_01_31-vol_6a200.deleted_backend_666_dc1_199_99_80 probe      Healthy 5/5
"""

BACKEND_LIST_RAW_RESPONSE_V6 = """
Backend name                   Admin      Probe                Last updated
template_4-ts-vol_1021a.first_service_2_dc1_199_11_80 probe      Healthy             5/5 Mon, 11 Apr 2022 16:03:08 GMT
template_4-ts-vol_1021a.first_service_3_dc1_199_12_80 probe      Sick             0/5 Mon, 11 Apr 2022 16:03:08 GMT
template_4-ts-vol_1021a.first_service_4_dc1_199_13_80 probe      Healthy             5/5 Mon, 11 Apr 2022 16:03:08 GM
template_4-ts-vol_1021a.del_backend_666_dc1_199_99_80 probe      Healthy             5/5 Mon, 11 Apr 2022 16:03:08 GMT
"""


EXPECTED_BACKEND_TO_STATUS_MAP_V4 = {
    '192.168.199.10:80': 'Healthy',
    '192.168.199.11:80': 'Sick',
    '192.168.199.12:80': 'Healthy'
}

EXPECTED_BACKEND_TO_STATUS_MAP_V6 = {
    '192.168.199.11:80': 'Healthy',
    '192.168.199.12:80': 'Sick',
    '192.168.199.13:80': 'Healthy'
}

EXPECTED_MERGED_STATUS_MAP = {
    '192.168.199.10:80': 'Healthy',
    '192.168.199.11:80': 'Sick',
    '192.168.199.12:80': 'Sick',
    '192.168.199.13:80': 'Healthy'
}


class BackendStatusManagerTest(TestCase):
    def setUp(self):
        timestamp = datetime.datetime.utcnow().replace(tzinfo=utc, microsecond=0) - datetime.timedelta(seconds=1)
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
        Backend.objects.create(address='192.168.199.13', port=80, director=director, dc=dc, id=4)
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
        BackendStatusManager(Mock(), []).store_backend_statuses(backend_to_status_map)
        statuses = BackendStatus.objects.all()
        assert_equals(2, len(statuses))
        self.assert_status('192.168.199.11', 80, 'Sick', statuses[0])
        self.assert_status('192.168.199.12', 80, 'Healthy', statuses[1])

    def test_should_load_backend_statuses_from_varnish_4(self):
        self._generic_load_backend_statuses_from_varnish(
            BACKEND_LIST_RAW_RESPONSE_V4_1, EXPECTED_BACKEND_TO_STATUS_MAP_V4
        )

    def test_should_load_backend_statuses_from_varnish_6(self):
        self._generic_load_backend_statuses_from_varnish(
            BACKEND_LIST_RAW_RESPONSE_V6, EXPECTED_BACKEND_TO_STATUS_MAP_V6
        )

    def _generic_load_backend_statuses_from_varnish(self, backend_list_response, expected_result):
        timeout = 0.1
        varnish_server_mock = Mock()
        varnish_api_mock = Mock()
        varnish_api_mock.fetch.return_value = (None, backend_list_response)

        varnish_api_provider_mock = Mock()
        varnish_api_provider_mock.get_api.return_value = varnish_api_mock

        assert_equals(
            expected_result,
            BackendStatusManager(varnish_api_provider_mock, [varnish_server_mock], timeout).load_from_varnish()
        )
        varnish_api_provider_mock.get_api.assert_called_once_with(varnish_server_mock, timeout)

    def test_should_merge_backend_statuses_from_multiple_varnishes(self):
        timeout = 0.1
        servers = {
            'first': Mock(fetch=Mock(return_value=(None, BACKEND_LIST_RAW_RESPONSE_V4_1))),
            'second': Mock(fetch=Mock(return_value=(None, BACKEND_LIST_RAW_RESPONSE_V6)))
        }

        varnish_api_provider_mock = Mock()
        varnish_api_provider_mock.get_api = Mock(side_effect=lambda s, _: servers[s])

        assert_equals(
            EXPECTED_MERGED_STATUS_MAP,
            BackendStatusManager(varnish_api_provider_mock, servers.keys(), timeout).load_from_varnish()
        )

    def test_should_refresh_backend_statuses(self):
        backend_to_status_map = {
            '192.168.199.11:80': 'Sick',
            '192.168.199.12:80': 'Healthy'
        }
        with patch('vaas.monitor.health.BackendStatusManager.load_from_varnish', return_value=backend_to_status_map):
            BackendStatusManager(Mock(), []).refresh_statuses()
            statuses = BackendStatus.objects.all()
            assert_equals(2, len(statuses))
            self.assert_status('192.168.199.11', 80, 'Sick', statuses[0])
            self.assert_status('192.168.199.12', 80, 'Healthy', statuses[1])
