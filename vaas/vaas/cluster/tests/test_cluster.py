# -*- coding: utf-8 -*-
from django.utils import timezone
from unittest.mock import patch, call, Mock
from django.test import TestCase

from vaas.cluster.forms import VclTemplateModelForm
from vaas.cluster.models import Dc, LogicalCluster, VarnishServer, VclTemplate
from vaas.cluster.cluster import connect_command, connect_status, validate_vcl_command, VarnishCluster, \
    ServerExtractor, ParallelRenderer, ParallelLoader, VarnishApiProvider, VclLoadException
from vaas.vcl.loader import VclLoader, VclStatus
from vaas.vcl.renderer import Vcl
from vaas.api.client import VarnishApi, VarnishApiReadException

dc = Dc(name='Tokyo', symbol='dc2')
cluster1 = LogicalCluster(name='cluster1', id=1)
cluster2 = LogicalCluster(name='cluster2', id=2)
cluster3 = LogicalCluster(name='cluster3', id=3)

servers = [
    VarnishServer(
        ip='127.0.0.1', port='6082', hostname='localhost-1', secret='secret-1', dc=dc, cluster=cluster1, status='active'
    ),
    VarnishServer(
        ip='127.0.0.2', port='6083', hostname='localhost-2', secret='secret-2', dc=dc, cluster=cluster2, status='active'
    ),
    VarnishServer(
        ip='127.0.0.3', port='6084', hostname='localhost-3', secret='secret-3', dc=dc, cluster=cluster3, status='active'
    ),
]

query_set = Mock()
query_set.prefetch_related = Mock(return_value=servers)

sample_vcl = Vcl('Test-content', name='test')


def test_should_return_connection_status_for_active_server():
    server = VarnishServer(pk=11, ip='127.0.0.1', port='6082', status='active')
    varnish_api_mock = Mock(daemon_version=Mock(return_value='varnish-7.0.3'))

    with patch.object(VarnishApiProvider, 'get_api', return_value=varnish_api_mock):
        assert 'varnish-7.0.3' == connect_status(server)

    varnish_api_mock.daemon_version.assert_called_once()


def test_should_return_object_status_for_inactive_server():
    for inactive_status in ('maintenance', 'disabled',):
        inactive_server = VarnishServer(pk=11, ip='127.0.0.1', port='6082', status=inactive_status)
        assert inactive_status == connect_status(inactive_server)


def test_command_should_return_connection_statuses_for_each_server():
    statuses = {
        11: 'varnish-7.0.3',
        12: 'maintenance',
    }
    db_servers = [
        VarnishServer(pk=11),
        VarnishServer(pk=12)
    ]
    with patch('vaas.cluster.cluster.VarnishServer.objects.filter', Mock(return_value=db_servers)):
        with patch('vaas.cluster.cluster.connect_status', Mock(side_effect=lambda s: statuses[s.pk])):
            result = connect_command([11, 12])
            assert 2 == len(result)
            assert 'varnish-7.0.3', result[11]
            assert 'maintenance', result[12]


def test_if_vcl_validation_returns_ok_for_template_not_linked_to_any_servers():
    expected_result = {
        'is_valid': True,
        'servers_num': 0,
    }
    result = validate_vcl_command(None, VclTemplate())
    assert expected_result == result


def test_if_vcl_validation_returns_fail_for_vcl_that_can_not_be_loaded():
    expected_result = {
        'is_valid': False,
        'servers_num': 1,
        'error': {
            'message': 'compilation failed',
            'type': "<class 'vaas.cluster.exceptions.VclLoadException'>",
        }
    }
    db_servers = [
        VarnishServer(pk=11),
    ]
    exclude_mock = Mock(filter=Mock(return_value=Mock(prefetch_related=Mock(return_value=db_servers))))
    with patch(
            'vaas.cluster.cluster.VarnishServer.objects.exclude',
            Mock(return_value=exclude_mock)):
        with patch.object(ParallelRenderer, 'render_vcl_for_servers', return_value=Mock()):
            with patch.object(ParallelLoader, 'load_vcl_list', side_effect=VclLoadException("compilation failed")):
                result = validate_vcl_command(None, VclTemplate())
                assert expected_result == result


def test_if_vcl_validation_returns_ok_for_vcl_that_is_successfully_loaded():
    expected_result = {
        'is_valid': True,
        'servers_num': 1
    }
    db_servers = [
        VarnishServer(pk=11),
    ]
    exclude_mock = Mock(filter=Mock(return_value=Mock(prefetch_related=Mock(return_value=db_servers))))
    with patch(
            'vaas.cluster.cluster.VarnishServer.objects.exclude',
            Mock(return_value=exclude_mock)):
        with patch.object(ParallelRenderer, 'render_vcl_for_servers', return_value=Mock()):
            with patch.object(ParallelLoader, 'load_vcl_list', return_value=Mock()):
                result = validate_vcl_command(None, VclTemplate())
                assert expected_result == result


class ServerExtractorTest(TestCase):
    @patch('vaas.cluster.cluster.VarnishServer.objects.exclude', Mock(return_value=query_set))
    def test_should_extract_servers_by_touched_clusters(self):
        touched_clusters = [cluster1, cluster2]
        expected_extracted_servers = [servers[0], servers[1]]

        assert ServerExtractor().extract_servers_by_clusters(touched_clusters) == expected_extracted_servers


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

                assert 3 == len(api_objects)
                assert expected_construct_args == construct_mock.call_args_list

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

        assert ParallelRenderer().render_vcl_for_servers('test', servers_list) == expected_vcl_list


class ParallelLoaderTest(TestCase):

    def test_should_load_vcl_list_to_associated_servers(self):
        first_vcl = Vcl('Test-1', name='test-1')
        second_vcl = Vcl('Test-2', name='test-2')
        vcl_list = [(servers[0], first_vcl), (servers[1], second_vcl)]

        with patch.object(VarnishApiProvider, 'get_api') as get_api_mock:
            with patch.object(VclLoader, 'load_new_vcl') as load_vcl_mock:
                ParallelLoader().load_vcl_list(vcl_list)
                assert [call(first_vcl), call(second_vcl)] == load_vcl_mock.call_args_list
                assert [call(servers[0]), call(servers[1])] == get_api_mock.call_args_list

    def test_should_load_vcl_to_associated_servers_and_force_servers_to_discard_properly_loaded_vcls(self):
        first_vcl = Vcl('Test-1', name='test-1')
        second_vcl = Vcl('Test-2', name='test-2')
        vcl_list = [(servers[0], first_vcl), (servers[1], second_vcl)]

        with patch.object(VarnishApiProvider, 'get_api') as get_api_mock:
            with patch.object(VclLoader, 'load_new_vcl') as load_vcl_mock:
                load_vcl_mock.side_effect = [VclStatus.OK, VclStatus.ERROR]
                with patch.object(VclLoader, 'discard_unused_vcls') as discard_mock:
                    with self.assertRaises(VclLoadException):
                        ParallelLoader().load_vcl_list(vcl_list, force_discard=True)

                    assert [call(first_vcl), call(second_vcl)] == load_vcl_mock.call_args_list
                    assert [call(servers[0]), call(servers[1])] == get_api_mock.call_args_list
                    assert 1 == discard_mock.call_count

    def test_should_return_loaded_vcl_list_which_should_be_use_on_servers(self):
        first_vcl = Vcl('Test-1', name='test-1')
        second_vcl = Vcl('Test-2', name='test-2')
        vcl_list = [(servers[1], first_vcl), (servers[2], second_vcl)]

        with patch.object(VarnishApiProvider, 'get_api'):
            with patch.object(VclLoader, 'load_new_vcl', return_value=VclStatus.OK):
                to_use = ParallelLoader().load_vcl_list(vcl_list)
                assert len(to_use) == 2
                self.assert_loaded_vcl_contains_proper_vcl_and_server(to_use[0], first_vcl, servers[1])
                self.assert_loaded_vcl_contains_proper_vcl_and_server(to_use[1], second_vcl, servers[2])

    def test_should_raise_custom_exception_if_error_occurred_while_loading_vcl(self):
        first_vcl = Vcl('Test-1', name='test-1')
        vcl_list = [(servers[1], first_vcl)]
        with patch.object(VarnishApiProvider, 'get_api'):
            with patch.object(VclLoader, 'load_new_vcl', return_value=VclStatus.ERROR):
                with self.assertRaises(VclLoadException):
                    ParallelLoader().load_vcl_list(vcl_list)

    def test_should_raise_custom_exception_if_timeout_occurred_while_loading_vcl(self):
        first_vcl = Vcl('Test-1', name='test-1')
        vcl_list = [(servers[1], first_vcl)]
        with patch.object(VarnishApiProvider, 'get_api'):
            with patch.object(VclLoader, 'load_new_vcl', side_effect=VarnishApiReadException):
                with self.assertRaises(VclLoadException):
                    ParallelLoader().load_vcl_list(vcl_list)

    def test_should_raise_custom_exception_if_error_occurred_while_connecting_to_server(self):
        first_vcl = Vcl('Test-1', name='test-1')
        vcl_list = [(servers[1], first_vcl)]
        with patch.object(VarnishApi, '__init__', side_effect=Exception):
            with self.assertRaises(VclLoadException):
                ParallelLoader().load_vcl_list(vcl_list)

    def assert_loaded_vcl_contains_proper_vcl_and_server(self, loaded_vcl_tuple, expected_vcl, expected_server):
        vcl, loader, server = loaded_vcl_tuple
        assert vcl == expected_vcl
        assert server == expected_server

    def test_should_return_true_if_vcl_list_is_properly_used(self):
        loader_mock = Mock()
        loader_mock.use_vcl = Mock(return_value=VclStatus.OK)
        first_vcl = Vcl('Test-1', name='test-1')
        vcl_loaded_list = [(first_vcl, loader_mock, servers[1])]

        assert ParallelLoader().use_vcl_list('test', vcl_loaded_list)

    def test_should_return_false_if_vcl_list_is_properly_used(self):
        loader_mock = Mock()
        loader_mock.use_vcl = Mock(return_value=VclStatus.ERROR)
        first_vcl = Vcl('Test-1', name='test-1')
        vcl_loaded_list = [(first_vcl, loader_mock, servers[1])]

        assert not ParallelLoader().use_vcl_list('test', vcl_loaded_list)

    def test_should_discard_old_vcls(self):
        loader_mock = Mock()
        loader_mock.use_vcl = Mock(return_value=VclStatus.OK)
        loader_mock.discard_unused_vcls = Mock()
        first_vcl = Vcl('Test-1', name='test-1')
        vcl_loaded_list = [(first_vcl, loader_mock, servers[1])]

        ParallelLoader().use_vcl_list('test', vcl_loaded_list)
        assert [call()] == loader_mock.discard_unused_vcls.call_args_list

    def test_should_discard_error_loaded_vcl(self):
        loader_mock = Mock()
        loader_mock.load_vcl_list = Mock(side_effect=VclLoadException)
        loader_mock.discard_unused_vcls = Mock()

        try:
            loader_mock.load_vcl_list()
        except VclLoadException:
            loader_mock.discard_unused_vcls()

        assert [call()] == loader_mock.discard_unused_vcls.call_args_list

    def test_should_return_vcl_list_without_broken_server_items(self):
        first_vcl = Vcl('Test-1', name='test-1')
        second_vcl = Vcl('Test-2', name='test-2')
        cluster_with_partial_reload = LogicalCluster(name='cluster1', id=1, partial_reload=True)
        server = VarnishServer(ip='127.0.0.1', port='6082', hostname='localhost-1', secret='secret-1', dc=dc,
                               cluster=cluster_with_partial_reload, status='active')

        vcl_list = [(server, first_vcl), (servers[1], second_vcl)]

        with patch.object(VarnishApiProvider, 'get_api', side_effect=[VclLoadException, None]):
            with patch.object(VclLoader, 'load_new_vcl', return_value=VclStatus.OK):
                # as opposed to test:
                # test_should_raise_custom_exception_if_error_occurred_while_connecting_to_server
                # it DOES NOT raise any exception when cluster allow partial reloads
                # what is being tested implicitly there.
                to_use = ParallelLoader().load_vcl_list(vcl_list)
                assert len(to_use) == 1

    def test_should_return_vcl_list_without_servers_that_have_timed_out_while_loading_vcl(self):
        first_vcl = Vcl('Test-1', name='test-1')
        second_vcl = Vcl('Test-2', name='test-2')
        cluster_with_partial_reload = LogicalCluster(name='cluster1', id=1, partial_reload=True)
        server = VarnishServer(ip='127.0.0.1', port='6082', hostname='localhost-1', secret='secret-1', dc=dc,
                               cluster=cluster_with_partial_reload, status='active')

        vcl_list = [(server, first_vcl), (servers[1], second_vcl)]

        with patch.object(VarnishApiProvider, 'get_api'):
            with patch.object(VclLoader, 'load_new_vcl', side_effect=[VarnishApiReadException, VclStatus.OK]):
                # as opposed to test:
                # test_should_raise_custom_exception_if_timeout_occurred_while_loading_vcl
                # it DOES NOT raise any exception when cluster allow partial reloads
                # what is being tested implicitly there.
                to_use = ParallelLoader().load_vcl_list(vcl_list)
                assert len(to_use) == 1


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
                    assert varnish_cluster.load_vcl(start_processing_time, [])
                    """
                    Here we check if only previously loaded vcl-s are used
                    """
                    assert [call(start_processing_time, loaded_list)], use_vcl_mock.call_args_list

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
                        assert [] == use_vcl_mock.call_args_list


class VclTemplateModelFormTest(TestCase):

    def setUp(self):
        self.vcl_valid_template_data = {
            'name': 'vcl_name',
            'content': 'some content',
            'version': '4.0',
            'comment': 'new comment'
        }

        self.vcl_invalid_template_data = {
            'name': 'vcl_name',
            'content': 'some content',
            'version': '4.0',
            'comment': ''
        }

    def test_should_save_new_vcl_template_with_new_comment(self):
        form = VclTemplateModelForm(data=self.vcl_valid_template_data)
        self.assertTrue(form.is_valid())
        obj = form.save()
        self.assertEqual(obj.comment, self.vcl_valid_template_data['comment'])

    def test_should_raise_validation_exception_for_blank_comment_field(self):
        form = VclTemplateModelForm(data=self.vcl_invalid_template_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'comment': ['This field is required.']})

    def test_should_save_updated_vcl(self):
        form = VclTemplateModelForm(data=self.vcl_valid_template_data)
        self.assertTrue(form.is_valid())
        obj = form.save()
        self.assertEqual(obj.name, self.vcl_valid_template_data['name'])

        form = VclTemplateModelForm(instance=obj, data=self.vcl_valid_template_data)
        self.assertTrue(form.is_valid())

    def test_should_raise_validation_exception_for_not_updated_comment_field(self):
        form = VclTemplateModelForm(data=self.vcl_valid_template_data)
        self.assertTrue(form.is_valid())
        obj = form.save()
        self.assertEqual(obj.name, self.vcl_valid_template_data['name'])

        form = VclTemplateModelForm(instance=obj, data=self.vcl_invalid_template_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'comment': ['This field is required.']})
