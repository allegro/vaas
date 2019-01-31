# -*- coding: utf-8 -*-

from mock import *
from nose.tools import *
from django.test import TestCase
from vaas.vcl.loader import VclLoader, VclStatus
from vaas.vcl.renderer import Vcl


class VclLoaderTest(TestCase):

    @patch('vaas.api.client.VarnishApi')
    def test_vcl_is_not_changed(self, varnish_api_mock):
        varnish_api_mock.vcl_active_name.return_value = 'vcl-current-vol_cfff2'

        vcl = Vcl('vcl content')
        vcl.name = 'vcl-new-vol.cfff2'

        loader = VclLoader(varnish_api_mock)

        assert_false(loader.vcl_has_changed(vcl))

    @patch('vaas.api.client.VarnishApi')
    def test_vcl_is_changed(self, varnish_api_mock):
        varnish_api_mock.vcl_content_active.return_value = 'vcl old content'

        loader = VclLoader(varnish_api_mock)

        assert_true(loader.vcl_has_changed(Vcl('vcl content')))

    @patch('vaas.api.client.VarnishApi')
    def test_do_not_load_new_vcl_if_no_changes(self, varnish_api_mock):
        varnish_api_mock.vcl_active_name.return_value = 'vcl-current-vol_cfff4'
        vcl = Mock()
        vcl.name = 'vcl-new-vol_cfff4'

        loader = VclLoader(varnish_api_mock)

        assert_equals(VclStatus.NO_CHANGES, loader.load_new_vcl(vcl))

    @patch('vaas.api.client.VarnishApi')
    def test_do_not_load_new_vcl_if_it_can_not_be_compiled(self, varnish_api_mock):
        varnish_api_mock.vcl_content_active.return_value = 'vcl old content'
        varnish_api_mock.vcl_inline.return_value = [[400]]

        loader = VclLoader(varnish_api_mock)

        assert_equals(VclStatus.ERROR, loader.load_new_vcl(Vcl('vcl content')))

    @patch('vaas.api.client.VarnishApi')
    def test_load_new_vcl(self, varnish_api_mock):
        varnish_api_mock.vcl_content_active.return_value = 'vcl old content'
        varnish_api_mock.vcl_inline.return_value = [[200]]

        loader = VclLoader(varnish_api_mock)

        assert_equals(VclStatus.OK, loader.load_new_vcl(Vcl('vcl content')))

    @patch('vaas.api.client.VarnishApi')
    def test_use_new_vcl(self, varnish_api_mock):
        varnish_api_mock.vcl_content_active.return_value = 'vcl old content'
        varnish_api_mock.vcl_use.return_value = [[200]]

        loader = VclLoader(varnish_api_mock)

        assert_true(VclStatus.OK, loader.use_vcl(Vcl('vcl content')))

    @patch('vaas.api.client.VarnishApi')
    def test_do_not_discard_unused_vcl_if_not_exists(self, varnish_api_mock):
        varnish_api_mock.vcls.return_value = {'available': []}

        loader = VclLoader(varnish_api_mock)

        assert_equals(VclStatus.NO_CHANGES, loader.discard_unused_vcls())

    @patch('vaas.api.client.VarnishApi')
    def test_discard_unused_vcl_if_exists(self, varnish_api_mock):
        varnish_api_mock.vcls.return_value = {'available': ['unused-1', 'usused-2']}
        varnish_api_mock.vcl_discard.return_value = [[200]]

        loader = VclLoader(varnish_api_mock)

        assert_equals(VclStatus.OK, loader.discard_unused_vcls())
        assert_equals([call('unused-1'), call('usused-2')], varnish_api_mock.vcl_discard.call_args_list)

    @patch('vaas.api.client.VarnishApi')
    def test_return_error_if_cannot_discard_unused_vcl(self, varnish_api_mock):
        varnish_api_mock.vcls.return_value = {'available': ['unused-1', 'usused-2']}
        varnish_api_mock.vcl_discard.return_value = [[400]]

        loader = VclLoader(varnish_api_mock)

        assert_equals(VclStatus.ERROR, loader.discard_unused_vcls())
        assert_equals([call('unused-1'), call('usused-2')], varnish_api_mock.vcl_discard.call_args_list)

    @patch('vaas.api.client.VarnishApi')
    def test_should_suppress_varnish_command_execution_exception_if_proper_parameter_is_passed(self, varnish_api_mock):
        varnish_api_mock.vcl_content_active.return_value = 'vcl old content'
        varnish_api_mock.vcl_inline.side_effect = AssertionError()
        loader = VclLoader(varnish_api_mock, True)

        assert_equals(VclStatus.NO_CHANGES, loader.load_new_vcl(Vcl('vcl content')))
