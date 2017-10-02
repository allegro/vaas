import requests_mock
from django.test import TestCase

from vaas.cluster.coherency import OutdatedServerManager, OutdatedServer
from vaas.cluster.models import LogicalCluster, VclTemplate, Dc, VarnishServer


class OutdatedServerManagerTest(TestCase):
    def setUp(self):
        self.cluster = LogicalCluster.objects.create(name='cluster-coherency')
        self.cluster.current_vcls.add("current_version")
        self.template = VclTemplate.objects.create(name='template-coherency')
        self.dc = Dc.objects.create(name='dc', symbol='dc1-coh')

    def _create_varnish_server(self, ip, http_port, port, status='active'):
        return VarnishServer.objects.create(
            ip=ip, http_port=http_port, dc=self.dc, template=self.template, cluster=self.cluster, status=status
        )

    @requests_mock.mock()
    def test_should_filter_outdated_servers(self, m):
        outdated = self._create_varnish_server('127.0.0.1', 8080, 6082)
        coherent = self._create_varnish_server('127.0.0.2', 8080, 6082)
        m.get('http://127.0.0.1:8080/vaas/', json={"vcl_version": "outdated_version"})
        m.get('http://127.0.0.2:8080/vaas/', json={"vcl_version": "current_version"})
        self.assertEqual([(outdated, "outdated_version")], OutdatedServerManager().filter([outdated, coherent]))

    @requests_mock.mock()
    def test_should_load_outdated_servers_and_map_to_dto(self, m):
        outdated = self._create_varnish_server('127.0.0.1', 8080, 6082)
        coherent = self._create_varnish_server('127.0.0.2', 8080, 6082)
        m.get('http://127.0.0.1:8080/vaas/', json={"vcl_version": "outdated_version"})
        m.get('http://127.0.0.2:8080/vaas/', json={"vcl_version": "current_version"})

        expected_server = OutdatedServer(
            outdated.pk, u'127.0.0.1', 6082, u'dc1-coh', u'cluster-coherency', u'outdated_version'
        )

        self.assertEqual([expected_server], OutdatedServerManager().load('cluster-coherency'))

    @requests_mock.mock()
    def test_should_not_load_outdated_disabled_servers(self, m):
        outdated_disabled = self._create_varnish_server('127.0.0.1', 8080, 6082, status='disabled')
        outdated = self._create_varnish_server('127.0.0.2', 8080, 6082)
        m.get('http://127.0.0.1:8080/vaas/', json={"vcl_version": "outdated_version"})
        m.get('http://127.0.0.2:8080/vaas/', json={"vcl_version": "outdated_version"})

        expected_server = OutdatedServer(
            outdated.pk, u'127.0.0.2', 6082, u'dc1-coh', u'cluster-coherency', u'outdated_version'
        )

        self.assertEqual([expected_server], OutdatedServerManager().load('cluster-coherency'))
