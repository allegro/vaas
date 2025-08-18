# -*- coding: utf-8 -*-

from django.test import TestCase
from unittest.mock import patch, MagicMock
from tastypie.http import HttpCreated, HttpApplicationError

from vaas.cluster.cluster import VarnishCluster
from vaas.manager.middleware import VclRefreshState, VclRefreshMiddleware


class VclRefreshStateTest(TestCase):

    def test_should_return_default_value(self):
        non_existence_id = '1235'
        self.assertFalse(VclRefreshState.get_refresh(non_existence_id))

    def test_should_return_previously_set_value_and_clean_state(self):
        req_id = '1234'
        VclRefreshState.set_refresh(req_id, True)
        self.assertEqual({req_id: True}, VclRefreshState.refresh)
        self.assertTrue(VclRefreshState.get_refresh(req_id))
        self.assertEqual({}, VclRefreshState.refresh)


class VclRefreshMiddlewareTest(TestCase):
    def test_should_get_list_vcl_refresh_state_for_request_id(self):

        request = MagicMock(id='10')

        middleware = VclRefreshMiddleware(MagicMock())

        self.assertIsNone(middleware.process_request(request))
        self.assertEqual({'10': []}, VclRefreshState.refresh)
        middleware.process_response(request, None)

    def test_should_clear_state_on_response(self):
        request = MagicMock(id='10')

        middleware = VclRefreshMiddleware(MagicMock())
        middleware.process_request(request)
        self.assertEqual("test", middleware.process_response(request, "test"))
        self.assertEqual({}, VclRefreshState.refresh)

    def test_should_not_refresh_vcl_on_response_if_empty_cluster_list(self):
        request = MagicMock(id='10')

        middleware = VclRefreshMiddleware(MagicMock())
        middleware.process_request(request)
        clusters = []
        VclRefreshState.set_refresh(request.id, clusters)

        with patch.object(VarnishCluster, '__init__', return_value=None):
            with patch.object(
                VarnishCluster,
                'load_vcl',
                return_value=None
            ) as load_vcl_mock:
                middleware.process_response(request, None)
                self.assertEqual(0, len(load_vcl_mock.call_args_list))

    def test_should_return_error_message_if_exception_while_loading_vcl(self):
        with patch('vaas.cluster.cluster.load_vcl_task.delay', side_effect=Exception('load vcl failed')):
            request = MagicMock(id='10', session={})
            middleware = VclRefreshMiddleware(MagicMock())
            VclRefreshState.set_refresh('10', [MagicMock(id='1')])
            middleware.process_response(request, None)
            self.assertIn('error_message', request.session)
            self.assertEqual('Exception: load vcl failed', request.session['error_message'])

    def test_should_return_error_message_in_tastypie_if_exception_while_loading_vcl(self):
        with patch('vaas.cluster.cluster.load_vcl_task.delay', side_effect=Exception('load vcl failed')):
            request = MagicMock(id='10', session={})
            middleware = VclRefreshMiddleware(MagicMock())
            VclRefreshState.set_refresh('10', [MagicMock(id='1')])
            response = middleware.process_response(request, HttpCreated())
            self.assertTrue(isinstance(response, HttpApplicationError))
            self.assertEqual(b'Exception: load vcl failed', response.content)
