# -*- coding: utf-8 -*-

from django.utils import timezone
from mock import patch, call, Mock
from nose.tools import assert_true, assert_false, assert_equals, assert_list_equal, raises
from django.test import TestCase

from vaas.cluster.models import VarnishServer, Dc, LogicalCluster
from vaas.cluster.cluster import VarnishCluster, ServerExtractor, ParallelRenderer, ParallelLoader, \
    VarnishApiProvider, VclLoadException, PartialParallelLoader
from vaas.vcl.loader import VclLoader, VclStatus
from vaas.vcl.renderer import VclRenderer, Vcl
from vaas.api.client import VarnishApi

dc = Dc(name='Tokyo', symbol='dc2')
cluster1 = LogicalCluster(name='cluster1')
cluster2 = LogicalCluster(name='cluster2')
cluster3 = LogicalCluster(name='cluster3')

servers = [
    VarnishServer(ip='127.0.0.1', port='6082', hostname='localhost-1', secret='secret-1', dc=dc, cluster=cluster1),
    VarnishServer(ip='127.0.0.2', port='6083', hostname='localhost-2', secret='secret-2', dc=dc, cluster=cluster2),
    VarnishServer(ip='127.0.0.3', port='6084', hostname='localhost-3', secret='secret-3', dc=dc, cluster=cluster3),
]

query_set = Mock()
query_set.prefetch_related = Mock(return_value=servers)

sample_vcl = Vcl('Test-content', name='test')


class ServerExtractorTest(TestCase):
    @patch('vaas.cluster.cluster.VarnishServer.objects.filter', Mock(return_value=query_set))
    def test_should_extract_servers_by_touched_clusters(self):
        touched_clusters = [cluster1, cluster2]
        expected_extracted_servers = [servers[0], servers[1]]

        assert_equals(ServerExtractor().extract_servers_by_clusters(touched_clusters), expected_extracted_servers)


class VarnishApiProviderTest(TestCase):

    def test_should_create_varnish_api_clients_for_all_servers(self):
        expected_construct_args = [
            call(['127.0.0.1', '6082', 1.0], 'secret-1'),
            call(['127.0.0.2', '6083', 1.0], 'secret-2'),
            call(['127.0.0.3', '6084', 1.0], 'secret-3')]
        sample_extractor = Mock(servers=servers)

        with patch('vaas.cluster.cluster.ServerExtractor', Mock(return_value=sample_extractor)):
                with patch.object(VarnishApi, '__init__', return_value=None) as construct_mock:
                    varnish_cluster = VarnishApiProvider()
                    api_objects = []
                    for api in varnish_cluster.get_varnish_api():
                        """
                        Workaround - we cannot mock __del__ method:
                        https://docs.python.org/3/library/unittest.mock.html

                        We inject sock field to eliminate warning raised by cleaning actions in __del__ method
                        """
                        api.sock = None
                        api_objects.append(api)

                    assert_equals(3, len(api_objects))
                    assert_list_equal(expected_construct_args, construct_mock.call_args_list)

    def test_should_create_varnish_api_for_connected_servers(self):
        expected_construct_args = [
            call(['127.0.0.1', '6082', 1.0], 'secret-1'),
            call(['127.0.0.2', '6083', 1.0], 'secret-2'),
            call(['127.0.0.3', '6084', 1.0], 'secret-3')]
        sample_extractor = Mock(servers=servers)

        api_init_side_effect = {
            'secret-1': Exception(),
            'secret-2': None,
            'secret-3': None
        }

        with patch('vaas.cluster.cluster.ServerExtractor', Mock(return_value=sample_extractor)):
            with patch.object(
                VarnishApi, '__init__', side_effect=lambda host_port_timeout, secret: api_init_side_effect[secret]
            ) as construct_mock:
                with patch('telnetlib.Telnet.close', Mock()):
                    varnish_cluster = VarnishApiProvider()
                    api_objects = []
                    for api in varnish_cluster.get_connected_varnish_api():
                        """
                        Workaround - we cannot mock __del__ method:
                        https://docs.python.org/3/library/unittest.mock.html

                        We inject sock field to eliminate warning raised by cleaning actions in __del__ method
                        """
                        api.sock = None
                        api_objects.append(api)

                    assert_equals(2, len(api_objects))
                    assert_list_equal(expected_construct_args, construct_mock.call_args_list)

    def test_should_throw_vcl_load_exception_on_any_error_while_connecting_to_varnish_api(self):
        with patch.object(VarnishApi, '__init__', side_effect=Exception):
            with patch.object(VarnishApi, '__del__'):
                varnish_cluster = VarnishApiProvider()
                with self.assertRaises(VclLoadException):
                    varnish_cluster.get_api(servers[0])


class ParallelRendererTest(TestCase):

    @patch('vaas.cluster.cluster.VclRenderer.render', Mock(return_value=sample_vcl))
    def test_should_render_vcls_for_each_passed_server(self):
        servers_list = [servers[0], servers[1]]
        expected_vcl_list = [(servers[0], sample_vcl), (servers[1], sample_vcl)]

        assert_list_equal(ParallelRenderer().render_vcl_for_servers('test', servers_list), expected_vcl_list)


class ParallelLoaderTest(TestCase):

    def test_should_load_vcl_list_to_associated_servers(self):
        first_vcl = Vcl('Test-1', name='test-1')
        second_vcl = Vcl('Test-2', name='test-2')
        vcl_list = [(servers[0], first_vcl), (servers[1], second_vcl)]

        with patch.object(VarnishApiProvider, 'get_api') as get_api_mock:
            with patch.object(VclLoader, 'load_new_vcl') as load_vcl_mock:
                ParallelLoader().load_vcl_list(vcl_list)
                assert_equals([call(first_vcl), call(second_vcl)], load_vcl_mock.call_args_list)
                assert_equals([call(servers[0]), call(servers[1])], get_api_mock.call_args_list)

    def test_should_return_loaded_vcl_list_which_should_be_use_on_servers(self):
        first_vcl = Vcl('Test-1', name='test-1')
        second_vcl = Vcl('Test-2', name='test-2')
        vcl_list = [(servers[1], first_vcl), (servers[2], second_vcl)]

        with patch.object(VarnishApiProvider, 'get_api'):
            with patch.object(VclLoader, 'load_new_vcl', return_value=VclStatus.OK):
                to_use = ParallelLoader().load_vcl_list(vcl_list)
                assert_equals(len(to_use), 2)
                self.assert_loaded_vcl_contains_proper_vcl_and_server(to_use[0], first_vcl, servers[1])
                self.assert_loaded_vcl_contains_proper_vcl_and_server(to_use[1], second_vcl, servers[2])

    @raises(VclLoadException)
    def test_should_raise_custom_exception_if_error_occurred_while_loading_vcl(self):
        first_vcl = Vcl('Test-1', name='test-1')
        vcl_list = [(servers[1], first_vcl)]
        with patch.object(VarnishApiProvider, 'get_api'):
            with patch.object(VclLoader, 'load_new_vcl', return_value=VclStatus.ERROR):
                ParallelLoader().load_vcl_list(vcl_list)

    @raises(VclLoadException)
    def test_should_raise_custom_exception_if_error_occurred_while_connecting_to_server(self):
        first_vcl = Vcl('Test-1', name='test-1')
        vcl_list = [(servers[1], first_vcl)]

        with patch.object(VarnishApiProvider, 'get_api'):
            ParallelLoader().load_vcl_list(vcl_list)

    def assert_loaded_vcl_contains_proper_vcl_and_server(self, loaded_vcl_tuple, expected_vcl, expected_server):
        vcl, loader, server = loaded_vcl_tuple
        assert_equals(vcl, expected_vcl)
        assert_equals(server, expected_server)

    def test_should_return_true_if_vcl_list_is_properly_used(self):
        loader_mock = Mock()
        loader_mock.use_vcl = Mock(return_value=VclStatus.OK)
        first_vcl = Vcl('Test-1', name='test-1')
        vcl_loaded_list = [(first_vcl, loader_mock, servers[1])]

        assert_true(ParallelLoader().use_vcl_list('test', vcl_loaded_list))

    def test_should_return_false_if_vcl_list_is_properly_used(self):
        loader_mock = Mock()
        loader_mock.use_vcl = Mock(return_value=VclStatus.ERROR)
        first_vcl = Vcl('Test-1', name='test-1')
        vcl_loaded_list = [(first_vcl, loader_mock, servers[1])]

        assert_false(ParallelLoader().use_vcl_list('test', vcl_loaded_list))

    def test_should_discard_old_vcls(self):
        loader_mock = Mock()
        loader_mock.use_vcl = Mock(return_value=VclStatus.OK)
        loader_mock.discard_unused_vcls = Mock()
        first_vcl = Vcl('Test-1', name='test-1')
        vcl_loaded_list = [(first_vcl, loader_mock, servers[1])]

        ParallelLoader().use_vcl_list('test', vcl_loaded_list)

        assert_true([call()], loader_mock.discard_unused_vcls.call_args_list)


class PartialParallelLoaderTest(TestCase):
    def test_should_return_vcl_list_without_broken_server_items(self):
        first_vcl = Vcl('Test-1', name='test-1')
        vcl_list = [(servers[1], first_vcl)]

        with patch.object(VarnishApiProvider, 'get_api', side_effect=VclLoadException):
            # as opposed to test:
            # PartialLoaderTest#test_should_raise_custom_exception_if_error_occurred_while_connecting_to_server
            # it DOES NOT raise any exception what is being tested implicitly there.
            to_use = PartialParallelLoader().load_vcl_list(vcl_list)

            self.assertListEqual([], to_use)


class VarnishClusterTest(TestCase):

    def test_should_load_and_use_only_loaded_vcls(self):
        start_processing_time = timezone.now()
        vcl = Vcl('Test-content', name='test')

        loader_mock = Mock()
        loader_mock.use_vcl = Mock(return_value=VclStatus.OK)
        loader_mock.discard_unused_vcls = Mock()

        rendered_list = [(vcl, servers[0])]
        loaded_list = [(vcl, loader_mock, servers[0])]

        with patch.object(ParallelRenderer, 'render_vcl_for_servers', return_value=rendered_list):
            with patch.object(ParallelLoader, 'load_vcl_list', return_value=loaded_list):
                with patch.object(ParallelLoader, 'use_vcl_list', return_value=True) as use_vcl_mock:
                    varnish_cluster = VarnishCluster()
                    assert_true(varnish_cluster.load_vcl(start_processing_time, []))
                    """
                    Here we check if only previously loaded vcl-s are used
                    """
                    assert_list_equal([call(start_processing_time, loaded_list)], use_vcl_mock.call_args_list)

    def test_should_not_use_vcls_on_error_while_loading_vcl(self):
        vcl = Vcl('Test-content', name='test')

        rendered_list = [(vcl, servers[0])]

        with patch.object(ParallelRenderer, 'render_vcl_for_servers', return_value=rendered_list):
            with patch.object(ParallelLoader, 'load_vcl_list', side_effect=VclLoadException):
                with patch.object(ParallelLoader, 'use_vcl_list', return_value=False) as use_vcl_mock:
                    varnish_cluster = VarnishCluster()
                    with self.assertRaises(VclLoadException):
                        varnish_cluster.load_vcl(timezone.now(), [])
                    """
                    Here we check if 'use' command is NOT sent to servers
                    """
                    assert_list_equal([], use_vcl_mock.call_args_list)
